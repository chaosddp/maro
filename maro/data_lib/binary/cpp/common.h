
#ifndef _MARO_DATALIB_COMMON_
#define _MARO_DATALIB_COMMON_

#include <unordered_map>
#include <string>

using namespace std;

namespace maro
{
    namespace datalib
    {
        using UCHAR = unsigned char;
        using ULONGLONG = unsigned long long;
        using UINT = uint32_t;

        /*
        4 bytes - identifier "maro"
        1 byte - file type (0: reserved, 1: binary, 2: index)
        4 bytes - converter version
        4 bytes - file version
        2 bytes - custimized file type (2 char)
        8 bytes - total items
        4 bytes - item size
        1 byte - utc offset
        8 bytes - start timestamp (real)
        8 bytes - end timestamp (real)
        4 bytes - meta size (meta just follow header)
        32 bytes - reserved
        */
        struct BinHeader
        {
            unsigned char file_type;

            char custom_file_type[3]{"NA"};
            char identifier[5]{"MARO"};
            char utc_offset{0};

            UINT converter_version{0U};
            UINT file_version{0U};
            UINT item_size{0U};
            UINT meta_size{0ULL};

            ULONGLONG total_items{0ULL};
            ULONGLONG start_timestamp{0ULL};
            ULONGLONG end_timestamp{0ULL};

            ULONGLONG reserved1{0ULL};
            ULONGLONG reserved2{0ULL};
            ULONGLONG reserved3{0ULL};
            ULONGLONG reserved4{0ULL};

            // write to buffer, and return size wrote
            // size_t write(char *buffer);
        };

    } // namespace datalib

} // namespace maro

#endif