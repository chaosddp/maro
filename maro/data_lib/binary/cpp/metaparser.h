// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef _MARO_DATALIB_METAPARSER_
#define _MARO_DATALIB_METAPARSER_

#include <string>
#include <vector>
#include <unordered_map>

#include "toml11/toml.hpp"
#include "common.h"

using namespace std;

namespace maro
{
    namespace datalib
    {
        static unordered_map<string, pair<unsigned char, size_t>> field_dtype = {
            {"b", {0, sizeof(char)}},
            {"i2", {1, sizeof(short)}},
            {"i", {2, sizeof(int32_t)}},
            {"i4", {2, sizeof(int32_t)}},
            {"i8", {3, sizeof(unsigned long long)}},
            {"f", {4, sizeof(float)}},
            {"d", {5, sizeof(double)}}};

        struct Field
        {
            unsigned char type{2};
            uint32_t size{0U};
            uint32_t start_index{0U};
            string column;
            string alias;

            Field(string alias, string column, uint32_t size, uint32_t start_index);

            UINT write(char* buffer);
        };

        struct Meta
        {
            string timezone;

            vector<Field> fields;

            uint32_t itemsize();

            template<typename... Args>
            void add_field(Args&&... args);
        };

        // load meta and parse, return fields info
        class MetaParser
        {

        public:
            MetaParser();

            // do use rvalue ref to call this
            void parse(string meta_file, Meta &meta);
        };
    } // namespace datalib

} // namespace maro

#endif