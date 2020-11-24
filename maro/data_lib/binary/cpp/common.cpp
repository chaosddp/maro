
#include "common.h"

namespace maro
{
    namespace datalib
    {

#define WriteToBuffer(size, src) \
    length = size; \
    memcpy(&buffer[offset], &src, length); \
    offset += length;

        size_t BinHeader::write(char *buffer)
        {
            size_t offset = 0ULL;
            size_t length = 0ULL;

            WriteToBuffer(strlen(identifier), identifier)
            WriteToBuffer(sizeof(unsigned char), file_type)
            WriteToBuffer(sizeof(UINT), converter_version)
            WriteToBuffer(sizeof(UINT), file_version)
            WriteToBuffer(strlen(custom_file_type), custom_file_type)
            WriteToBuffer(sizeof(ULONGLONG), total_items)
            WriteToBuffer(sizeof(UINT), item_size)
            WriteToBuffer(sizeof(ULONGLONG), start_timestamp)
            WriteToBuffer(sizeof(ULONGLONG), end_timestamp)
            WriteToBuffer(sizeof(ULONGLONG), meta_size)

            WriteToBuffer(sizeof(ULONGLONG), reserved1)
            WriteToBuffer(sizeof(ULONGLONG), reserved2)
            WriteToBuffer(sizeof(ULONGLONG), reserved3)
            WriteToBuffer(sizeof(ULONGLONG), reserved4)

            return offset;
        }
    } // namespace datalib

} // namespace maro
