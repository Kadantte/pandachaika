import os
from typing import Optional

import requests

from core.base.types import DataDict
from core.base.utilities import calc_crc32, get_base_filename_string_from_gallery_data, \
    get_zip_fileinfo
from core.downloaders.handlers import BaseDownloader, BaseInfoDownloader
from viewer.models import Archive
from core.base.utilities import (available_filename,
                                 replace_illegal_name)
from . import constants


class ArchiveDownloader(BaseDownloader):

    type = 'archive'
    provider = constants.provider_name

    def start_download(self) -> None:

        if not self.gallery or not self.gallery.link or not self.gallery.archiver_key:
            return

        to_use_filename = get_base_filename_string_from_gallery_data(self.gallery)

        to_use_filename = replace_illegal_name(to_use_filename)

        self.gallery.filename = available_filename(
            self.settings.MEDIA_ROOT,
            os.path.join(
                self.own_settings.archive_dl_folder,
                to_use_filename + '.zip'))

        request_file = requests.get(
            self.gallery.archiver_key,
            stream='True',
            headers=self.settings.requests_headers,
            timeout=self.settings.timeout_timer,
            cookies=self.own_settings.cookies
        )

        filepath = os.path.join(self.settings.MEDIA_ROOT,
                                self.gallery.filename)
        with open(filepath, 'wb') as fo:
            for chunk in request_file.iter_content(4096):
                fo.write(chunk)

        self.gallery.filesize, self.gallery.filecount = get_zip_fileinfo(filepath)
        if self.gallery.filesize > 0:
            self.crc32 = calc_crc32(filepath)

            self.fileDownloaded = 1
            self.return_code = 1

        else:
            self.logger.error("Could not download archive")
            os.remove(filepath)
            self.return_code = 0

    def update_archive_db(self, default_values: DataDict) -> Optional['Archive']:

        if not self.gallery:
            return None

        values = {
            'title': self.gallery.title,
            'title_jpn': '',
            'zipped': self.gallery.filename,
            'crc32': self.crc32,
            'filesize': self.gallery.filesize,
            'filecount': self.gallery.filecount,
        }
        default_values.update(values)
        return Archive.objects.update_or_create_by_values_and_gid(
            default_values,
            self.gallery.gid,
            zipped=self.gallery.filename
        )


class InfoDownloader(BaseInfoDownloader):

    provider = constants.provider_name


API = (
    ArchiveDownloader,
    InfoDownloader,
)
