#include "metaparser.h"

namespace maro
{
    namespace datalib
    {
        Field::Field(string alias, string column, uint32_t size, uint32_t start_index) : alias(move(alias)), column(move(column)), size(move(size)), start_index(move(start_index))
        {
        }

        UINT Field::write(char *buffer)
        {
            return UINT();
        }

        uint32_t Meta::itemsize()
        {
            uint32_t size = 0;

            for (auto f : fields)
            {
                size += f.size;
            }

            return size;
        }

        template <typename... Args>
        void Meta::add_field(Args &&... args)
        {
            fields.emplace_back(args);
        }

        MetaParser::MetaParser()
        {
        }

        void MetaParser::parse(string meta_file, Meta &meta)
        {
            // load the file
            const auto data = toml::parse(meta_file);

            // find row definition
            const auto row = toml::find<vector<toml::table>>(data, "row");

            uint32_t offset = 0U;

            for (auto col : row)
            {
                // parse each column definition
                auto col_name = col["column"].as_string();
                auto type = col["type"].as_string();
                auto alias = col["alias"].as_string();

                auto kv = field_dtype.find(type);
                auto size = uint32_t(kv->second.second);

                offset += size;

                meta.fields.emplace_back(alias, col_name, size, offset);
            }

            meta.timezone = toml::find<string>(data, "timezone");
        }

    } // namespace datalib

} // namespace maro
