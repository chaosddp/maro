import functools


# decorator for class to extract fields into stream data
def csv_object(category, fields):
    def fields_wrapper(cls):
        class CsvObjectWrapper(cls):
            def __init__(self, *args, **kwargs):
                super(CsvObjectWrapper, self).__init__(*args, **kwargs)

            def _get_stream_data(self):
                data = [category]

                for field in fields:
                    data.append(getattr(self, field))

                return data


        return CsvObjectWrapper

    return fields_wrapper
