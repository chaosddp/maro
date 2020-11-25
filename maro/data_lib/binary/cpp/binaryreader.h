#ifndef _MARO_DATALIB_BINARYREADER_
#define _MARO_DATALIB_BINARYREADER_

#include <iostream>
#include <fstream>
#include <string>

#include "common.h"
#include "itemcontainer.h"

using namespace std;

namespace maro
{
    namespace datalib
    {

        class ConvertVersionNotMatch : public exception
        {
        };

        class BinaryReader
        {
        private:
            BinHeader _header;
            Meta _meta;

            ifstream _file;

            char _buffer[BUFFER_LENGTH];
            ItemContainer _item;

            long max_items_in_buffer{0};
            int cur_item_index{-1};

            void read_header();
            void read_meta();

        public:
            BinaryReader(string bin_file);
            ~BinaryReader();

            ItemContainer *next_item();

            const Meta* get_meta();
        };

    } // namespace datalib

} // namespace maro

#endif