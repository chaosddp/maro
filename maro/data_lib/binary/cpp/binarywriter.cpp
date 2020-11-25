// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include "binarywriter.h"

namespace maro
{
    namespace datalib
    {
        inline char calc_local_utc_offset()
        {
            time_t rawtime;
            struct tm *ptm;

            time(&rawtime);

            ptm = gmtime(&rawtime);

            auto t2 = mktime(ptm);

            return char((rawtime - t2) / SECONDS_PER_HOUR);
        }

        inline ULONGLONG to_timestamp(string &val_str, unsigned char local_utc_offset = 0, char utc_offset = 0)
        {
            // TODO: need to test on US timezone

            tm t{};
            istringstream ss(val_str);
            ss >> get_time(&t, "%Y-%m-%d %H:%M:%S");

            auto t3 = mktime(&t);

            struct tm *ptm;

            auto t4 = t3 + (local_utc_offset - utc_offset) * SECONDS_PER_HOUR;

            return t4;
        }

        inline short to_short(string &val_str)
        {
            return short(stoi(val_str));
        }

        inline int32_t to_int(string &val_str)
        {
            return int32_t(stoi(val_str));
        }

        inline LONGLONG to_long(string &val_str)
        {
            return stoll(val_str);
        }

        inline float to_float(string &val_str)
        {
            return stof(val_str);
        }

        inline double to_double(string &val_str)
        {
            return stod(val_str);
        }

        BinaryWriter::BinaryWriter(string output_folder, string file_name, string file_type, int32_t file_version)
        {
            local_utc_offset = calc_local_utc_offset();

            auto bin_file = output_folder + "/" + file_name + ".bin";

            _file.open(bin_file, ios::out | ios::binary);

            _header.file_type = FILE_TYPE_BIN;
            _header.converter_version = CONVERTER_VERSION;

            write_header();
        }

        BinaryWriter::~BinaryWriter()
        {
            // update header before close
            write_header();

            _file.flush();
            _file.close();
        }

        void BinaryWriter::load_meta(string meta_file)
        {
            MetaParser parser;

            parser.parse(meta_file, _meta);

            _header.item_size = _meta.itemsize();
            _header.utc_offset = _meta.utc_offset;

            write_meta();

            write_header();
        }

        void BinaryWriter::add_csv(string csv_file)
        {
            CSV csv;

            if (csv.mmap(csv_file))
            {
                const auto &header = csv.header();

                // construct the column to field mapping for each csv file
                construct_column_mapping(header);
                
                // max number of items in buffer
                auto max_items_num = floorl(BUFFER_LENGTH / _header.item_size);

                // current items in buffer
                auto cur_items_num = 0;

                auto colum_index = 0;

                for (const auto row : csv)
                {
                    auto length = 0;
                    auto offset = 0;
                    colum_index = 0;

                    for (const auto cell : row)
                    {
                        // cell.read_value()
                        auto iter = _col2field_map.find(colum_index);

                        if (iter != _col2field_map.end())
                        {
                            // we find the column
                            string v;

                            cell.read_value(v);

                            auto &field = _meta.fields[iter->second];

                            switch (field.type)
                            {
                            case 1:
                            {
                                // short
                                auto rv = to_short(v);
                                length = sizeof(short);
                                memcpy(&_buffer[offset], &rv, length);
                                offset += length;

                                break;
                            }
                            case 2:
                            {
                                // int
                                auto rv = to_int(v);
                                length = sizeof(int32_t);
                                memcpy(&_buffer[offset], &rv, length);
                                offset += length;

                                break;
                            }
                            case 3:
                            { // long
                                auto rv = to_long(v);
                                length = sizeof(LONGLONG);
                                memcpy(&_buffer[offset], &rv, length);
                                offset += length;

                                break;
                            }
                            case 4:
                            { // float
                                auto rv = to_float(v);
                                length = sizeof(float);
                                memcpy(&_buffer[offset], &rv, length);
                                offset += length;

                                break;
                            }
                            case 5:
                            { // double
                                auto rv = to_double(v);
                                length = sizeof(double);
                                memcpy(&_buffer[offset], &rv, length);
                                offset += length;

                                break;
                            }
                            case 6:
                            {
                                // timestamp
                                auto rv = to_timestamp(v, local_utc_offset, _meta.utc_offset);
                                length = sizeof(ULONGLONG);
                                memcpy(&_buffer[offset], &rv, length);
                                offset += length;

                                // update header
                                if (field.alias == "timestamp")
                                {
                                    if (_header.start_timestamp == 0ULL)
                                    {
                                        _header.start_timestamp = rv;

                                        cout << rv << endl;
                                    }

                                    _header.end_timestamp = rv;
                                }

                                break;
                            }
                            default:
                                break;
                            }
                        }

                        colum_index++;
                    }

                    if (offset > 0)
                    {
                        cur_items_num++;
                        _header.total_items++;

                        if(cur_items_num >= max_items_num)
                        {
                            _file.write(_buffer, cur_items_num * _header.item_size);

                            cur_items_num = 0;
                        }
                        
                    }
                }

                if(cur_items_num !=0)
                {
                    _file.write(_buffer, cur_items_num * _header.item_size);
                }
            }
        }

        // write header

        // write item

        void BinaryWriter::construct_column_mapping(const CSV::Row &header)
        {
            // clear first
            _col2field_map.clear();

            auto hi = 0;

            // try to match the headers with meta, and keep the index
            for (const auto h : header)
            {
                for (auto fi = 0; fi < _meta.fields.size(); fi++)
                {
                    const auto &field = _meta.fields[fi];
                    string hstr;

                    h.read_value(hstr);

                    if (hstr == field.column)
                    {
                        _col2field_map[hi] = fi;

                        break;
                    }
                }

                hi++;
            }
        }

#define WriteToBuffer(size, src)            \
    length = size;                          \
    memcpy(&_buffer[offset], &src, length); \
    offset += length;

        void BinaryWriter::write_header()
        {
            _file.seekp(0, ios::beg);

            size_t offset = 0ULL;
            size_t length = 0ULL;

            WriteToBuffer(strlen(_header.identifier), _header.identifier)
            WriteToBuffer(sizeof(unsigned char), _header.file_type)
            WriteToBuffer(sizeof(UINT), _header.converter_version)
            WriteToBuffer(sizeof(UINT), _header.file_version)
            WriteToBuffer(strlen(_header.custom_file_type), _header.custom_file_type)
            WriteToBuffer(sizeof(ULONGLONG), _header.total_items)
            WriteToBuffer(sizeof(UINT), _header.item_size)
            WriteToBuffer(sizeof(char), _header.utc_offset)
            WriteToBuffer(sizeof(ULONGLONG), _header.start_timestamp)
            WriteToBuffer(sizeof(ULONGLONG), _header.end_timestamp)
            WriteToBuffer(sizeof(ULONGLONG), _header.meta_size)

            WriteToBuffer(sizeof(ULONGLONG), _header.reserved1)
            WriteToBuffer(sizeof(ULONGLONG), _header.reserved2)
            WriteToBuffer(sizeof(ULONGLONG), _header.reserved3)
            WriteToBuffer(sizeof(ULONGLONG), _header.reserved4)

            _file.write(_buffer, offset);
            _file.seekp(0, ios::end);
        }

        void BinaryWriter::write_meta()
        {
            /*
            Each field info if a pair of name and index:

            4 bytes - start index (in bytes) in binary block
            1 byte - filed type
            2 bytes - field name length
            N bytes - filed name that length same as above specified
            */

            for (auto &field : _meta.fields)
            {
                size_t offset = 0ULL;
                size_t length = 0ULL;

                WriteToBuffer(sizeof(uint32_t), field.start_index)
                WriteToBuffer(sizeof(unsigned char), field.type) 
                WriteToBuffer(sizeof(uint32_t), field.size)

                auto alias_length = field.alias.size();

                WriteToBuffer(sizeof(unsigned short), alias_length)
                WriteToBuffer(alias_length, field.alias[0])

                _file.write(_buffer, offset);

                 _header.meta_size += offset;
            }
        }

    } // namespace datalib
} // namespace maro