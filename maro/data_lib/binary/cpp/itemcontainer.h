// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef _MARO_DATALIB_ITEM_CONTAINER_
#define _MARO_DATALIB_ITEM_CONTAINER_

#include "common.h"

namespace maro
{
  namespace datalib
  {
    template <typename T>
    struct ItemContainer_trait
    {
      typedef T type;
    };

    /*
    Binary reader will always return same container for all items,
    user should make sure to copy the return if need
    */
    class ItemContainer
    {
      char* _buffer{ nullptr };
      int _offset{ 0 };

    public:
      ItemContainer();
      ItemContainer(ItemContainer&& cntr) = delete;
      ItemContainer(const ItemContainer& writer) = delete;

      ~ItemContainer();

      void set_buffer(char* buffer);

      void set_offset(UINT offset);

      template <typename T>
      typename ItemContainer_trait<T>::type get(int offset);
    };
  } // namespace datalib

} // namespace maro

#endif
