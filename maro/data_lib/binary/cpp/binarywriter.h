// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef _MARO_DATALIB_BINARY_WRITER_
#define _MARO_DATALIB_BINARY_WRITER_

#include <time.h>
#include <iostream>
#include <fstream>
#include <string>
#include <map>

#include "csv2/csv2.hpp"
#include "metaparser.h"

using namespace std;

using CSV = csv2::Reader<csv2::delimiter<','>,
                         csv2::quote_character<'\"'>,
                         csv2::first_row_is_header<true>,
                         csv2::trim_policy::trim_whitespace>;

namespace maro
{
    namespace datalib
    {
        const string MARO = "maro";
        const unsigned char FILE_TYPE_BIN = 1;
        const unsigned char FILE_TYPE_INDEX = 2;
        const uint32_t CONVERTER_VERSION = 100;
        
        const int SECONDS_PER_HOUR = 60 * 60;
        static char local_utc_offset = MINCHAR;

        class BinaryWriter
        {
        public:
            BinaryWriter() = delete;
            BinaryWriter(const BinaryWriter &writer) = delete;
            BinaryWriter(string output_folder, string file_name, string file_type = "NA", int32_t file_version = 0);

            ~BinaryWriter();

            // load meta file, and generate meta info
            void load_meta(string meta_file);

            // load and convert
            void add_csv(string csv_file);

        private:
            // seams FILE is faster than ofstream
            ofstream _file;
            BinHeader _header;

            Meta _meta;

            char _buffer[4096];

            map<int, int> _col2field_map;

            void construct_column_mapping(const CSV::Row& header);
            void write_header();

            void write_meta();
            
        };
    } // namespace datalib

} // namespace maro

#endif