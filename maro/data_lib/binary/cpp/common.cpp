
#include "common.h"

namespace maro
{
    namespace datalib
    {
        Field::Field(string alias, string column, uint32_t size, uint32_t start_index, unsigned char dtype)
            : alias(move(alias)),
              column(move(column)),
              size(move(size)),
              start_index(move(start_index)),
              type(move(dtype))
        {
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
    } // namespace datalib

} // namespace maro
