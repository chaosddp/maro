// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include "binarywriter.h"

namespace maro
{
    namespace datalib
    {
        inline ULONGLONG to_timestamp(string &val_str)
        {
            return ULONGLONG();
        }
        inline short to_short(string &val_str)
        {
            return short();
        }
        inline int32_t to_int(string &val_str)
        {
            return int32_t();
        }
        inline LONGLONG to_long(string &val_str)
        {
            return LONGLONG();
        }
        inline float to_float(string &val_str)
        {
            return float();
        }
        inline double to_double(string &val_str)
        {
            return double();
        }
        inline void strip(string &str)
        {
            if (str.size() > 0)
            {
                if (str[0] == '\"')
                {
                    str.erase(0, 1);
                }

                if (str[str.size() - 1] == '\"')
                {
                    str.erase(str.size() - 1);
                }
            }

            
        }

        BinaryWriter::BinaryWriter(string output_folder, string file_name, string file_type, int32_t file_version)
        {
            auto bin_file = output_folder + "/" + file_name + ".bin";

            _file.open(bin_file, ios::out | ios::binary);

            _header.file_type = FILE_TYPE_BIN;
            
            write_header();
        }

        BinaryWriter::~BinaryWriter()
        {
            _file.flush();
            _file.close();
        }

        void BinaryWriter::load_meta(string meta_file)
        {
            MetaParser parser;

            parser.parse(meta_file, _meta);

            _header.item_size = _meta.itemsize();
            
        }

        void BinaryWriter::add_csv(string csv_file)
        {
            CSV csv;
            auto i = 0;

            if (csv.mmap(csv_file))
            {
                const auto &header = csv.header();

                construct_column_mapping(header);

                for (const auto row : csv)
                {
                    i = 0;

                    for (const auto cell : row)
                    {
                        // cell.read_value()
                        auto iter = _col2field_map.find(i);

                        if (iter != _col2field_map.end())
                        {
                            // we find the column
                            string v;

                            cell.read_value(v);

                            auto &field = _meta.fields[iter->second];

                            switch (field.type)
                            {
                            case 0:
                                // byte
                                break;
                            case 1:
                                // short
                                break;
                            case 2:
                                // int
                                break;
                            case 3:
                                // long
                                break;
                            case 4:
                                // float
                                break;
                            case 5:
                                // double
                                break;

                            default:
                                break;
                            }
                        }

                        i++;
                    }
                }
            }
        }

        // write header

        // write item

        void BinaryWriter::construct_column_mapping(const CSV::Row &header)
        {
            auto hi = 0;

            // try to match the headers with meta, and keep the index
            for (const auto h : header)
            {
                for (auto fi = 0; fi < _meta.fields.size(); fi++)
                {
                    const auto &field = _meta.fields[fi];
                    string hstr;

                    h.read_value(hstr);

                    strip(hstr);

                    if (hstr == field.column)
                    {
                        _col2field_map[hi] = fi;

                        break;
                    }
                }

                hi++;
            }
        }

        void BinaryWriter::write_header()
        {
            _file.seekp(0, ios::beg);

            auto size = _header.write(_buffer);

            _file.write(_buffer, size);
        }

    } // namespace datalib
} // namespace maro