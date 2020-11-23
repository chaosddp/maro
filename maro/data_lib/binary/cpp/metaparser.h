// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef _MARO_DATALIB_METAPARSER_
#define _MARO_DATALIB_METAPARSER_

#include <string>
#include <vector>

#include "toml11/toml.hpp"

using namespace std;

namespace maro
{
    namespace datalib
    {
        struct Field
        {
            string alias;
            string column;
            string type;

            Field(string alias, string column, string type);
        };

        struct Meta
        {
            string timezone;

            vector<Field> fields;
        };

        // load meta and parse, return fields info
        class MetaParser
        {

        public:
            MetaParser();

            // do use rvalue ref to call this
            Meta parse(string meta_file);
        };
    } // namespace datalib

} // namespace maro

#endif