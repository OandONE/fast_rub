class props:
    def __init__(self,data):
        self._data_ = data
    def __getattr__(self, name):
        return self.find_prop(keys=name)
    def __getitem__(self, key):
        return self._data_[key]
    def __lts__(self, update: list, *args, **kwargs):
        for index, element in enumerate(update):
            if isinstance(element, list):
                update[index] = self.__lts__(update=element)
            elif isinstance(element, dict):
                update[index] = props(data=element)
            else:
                update[index] = element
        return update
    def find_prop(self, keys, data_=None, *args, **kwargs):
        if data_ is None:
            data_ = self._data_
        if not isinstance(keys, list):
            keys = [keys]
        if isinstance(data_, dict):
            for key in keys:
                try:
                    update = data_[key]
                    if isinstance(update, dict):
                        update = props(data=update)
                    elif isinstance(update, list):
                        update = self.__lts__(update=update)
                    return update
                except KeyError:
                    pass
            data_ = data_.values()
        for value in data_:
            if isinstance(value, (dict, list)):
                try:
                    return self.find_prop(keys=keys, data_=value)
                except AttributeError:
                    return None
        return None
    def __str__(self) -> str:
        return str(self._data_)
    @property
    def status(self):
        """status for requests / وضعیت درخواست"""
        return self._data_["status"]
    @property
    def is_ok_status(self):
        return True if self.status == "OK" else False
