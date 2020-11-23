#include "metaparser.h"

namespace maro
{
    namespace datalib
    {
        Field::Field(string alias, string column, string type) : alias(alias), column(column), type(type)
        {
        }

        MetaParser::MetaParser()
        {
        }

        Meta MetaParser::parse(string meta_file)
        {
            auto meta = Meta();

            // load the file
            const auto data = toml::parse(meta_file);

            // find row definition
            const auto row = toml::find<vector<toml::table>>(data, "row");

            for (auto col : row)
            {
                // parse each column definition
                auto col_name = col["column"].as_string();
                auto type = col["type"].as_string();
                auto alias = col["alias"].as_string();

                meta.fields.emplace_back(alias, col_name, type);
            }

            meta.timezone = toml::find<string>(data, "timezone");

            return meta;
        }

    } // namespace datalib

} // namespace maro
