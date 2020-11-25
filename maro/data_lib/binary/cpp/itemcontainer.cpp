#include "itemcontainer.h"

namespace maro
{
    namespace datalib
    {
        ItemContainer::ItemContainer()
        {}

        void ItemContainer::set_buffer(char *buffer)
        {
            _buffer = buffer;
        }

        ItemContainer::~ItemContainer()
        {
            _buffer = nullptr;
        }

        void ItemContainer::set_offset(UINT offset)
        {
            _offset = offset;
        }

        template <>
        int32_t ItemContainer::get<int32_t>(int offset)
        {
            int32_t r = 0;

            memcpy(&r, &_buffer[offset], sizeof(int32_t));

            return r;
        }

        template <>
        float ItemContainer::get<float>(int offset)
        {
            float r = 0;

            memcpy(&r, &_buffer[offset], sizeof(float));

            return r;
        }

        template <>
        double ItemContainer::get<double>(int offset)
        {
            double r = 0;

            memcpy(&r, &_buffer[offset], sizeof(double));

            return r;
        }

        template <>
        short ItemContainer::get<short>(int offset)
        {
            short r = 0;

            memcpy(&r, &_buffer[offset], sizeof(short));

            return r;
        }

        template <>
        ULONGLONG ItemContainer::get<ULONGLONG>(int offset)
        {
            ULONGLONG r = 0ULL;

            memcpy(&r, &_buffer[offset], sizeof(ULONGLONG));

            return r;
        }
    } // namespace datalib

} // namespace maro
