from cloudinary_storage.storage import MediaCloudinaryStorage

class RawMediaCloudinaryStorage(MediaCloudinaryStorage):
    def _get_options(self, name):
        options = super()._get_options(name)
        options['resource_type'] = 'raw'
        return options