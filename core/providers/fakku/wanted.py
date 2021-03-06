import re
import time
import typing
import urllib.parse

from bs4 import BeautifulSoup
from django.db.models import QuerySet

from core.base.types import RealLogger, DataDict
from core.base.utilities import request_with_retries, format_title_to_wanted_search
from viewer.models import Gallery, WantedGallery, Provider, Artist
from . import constants

if typing.TYPE_CHECKING:
    from core.base.setup import Settings


def wanted_generator(settings: 'Settings', ext_logger: RealLogger, attrs: QuerySet):
    own_settings = settings.providers[constants.provider_name]

    queries: DataDict = {}

    for attr in attrs.filter(name__startswith='wanted_params_'):

        attr_info = attr.name.replace('wanted_params_', '')
        query_name, attr_name = attr_info.split("_", maxsplit=1)

        if query_name not in queries:
            queries[query_name] = {
                'page': 1
            }

        queries[query_name].update({attr_name: attr.value})

    provider, provider_created = Provider.objects.get_or_create(
        slug=constants.provider_name, defaults={'name': constants.provider_name}
    )

    parser = settings.provider_context.get_parsers(settings, ext_logger, filter_name=constants.provider_name)[0]

    rounds = 0

    # Values that can be set:
    # subpath: subpath to search. (books, tags/doujin)
    # container_tag: Tag for the main container for each individual link. (div, span)
    # container_attribute_name: Attribute name for the main container for each individual link. (class)
    # container_attribute_value: Attribute value for the main container for each individual link. (content-meta)
    # link_tag: Tag for the link container inside the container. (a, span)
    # link_attribute_name: Attribute name for the link container inside the container. (a, span)
    # link_attribute_value: Attribute value for the link container inside the container. (href, src)
    # url_attribute_name: Attribute name for the URL container inside the container. (href, src)
    # link_attribute_get_text: Boolean to specify if it should get the text inside a tag. (True, False)
    for query_name, query_values in queries.items():

        while True:

            rounds += 1

            if rounds > 1:
                time.sleep(settings.wait_timer)

            ext_logger.info('Querying {} for auto wanted galleries, query name: {}, options: {}'.format(
                constants.provider_name, query_name, str(query_values))
            )

            if 'subpath' not in query_values:
                ext_logger.error('Cannot query without setting a subpath for {}'.format(query_name))
                break
            subpath = query_values['subpath']

            if not {'container_tag', 'container_attribute_name', 'container_attribute_value'}.issubset(query_values.keys()):
                ext_logger.error('Cannot query without html container definition for {}'.format(query_name))
                break
            container_tag = query_values['container_tag']
            container_attribute_name = query_values['container_attribute_name']
            container_attribute_value = query_values['container_attribute_value']

            get_text_from_container = False
            link_tag = ''
            link_attribute_name = ''
            link_attribute_value = ''
            url_attribute_name = ''

            if 'link_attribute_get_text' in query_values and query_values['link_attribute_get_text']:
                get_text_from_container = True
            else:
                if not {'link_tag', 'link_attribute_name', 'link_attribute_value', 'url_attribute_name'}.issubset(
                        query_values.keys()):
                    ext_logger.error('Cannot query without link container definition for {}'.format(query_name))
                    break
                link_tag = query_values['link_tag']
                link_attribute_name = query_values['link_attribute_name']
                if link_attribute_name == 'class':
                    link_attribute_name = 'class_'
                link_attribute_value = query_values['link_attribute_value']
                url_attribute_name = query_values['url_attribute_name']

            full_url = urllib.parse.urljoin("{}/".format(subpath), "page/{}".format(query_values['page']))

            link = urllib.parse.urljoin(constants.main_url, full_url)

            response = request_with_retries(
                link,
                {
                    'headers': settings.requests_headers,
                    'timeout': settings.timeout_timer,
                    'cookies': own_settings.cookies
                },
                post=False,
                logger=ext_logger
            )

            if not response:
                ext_logger.error('Got to page {}, but did not get a response, stopping'.format(query_values['page']))
                break

            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            gallery_containers = soup.find_all(
                container_tag,
                **{container_attribute_name: re.compile(container_attribute_value)}
            )

            gallery_links: typing.List[str] = []
            gallery_gids: typing.List[str] = []

            for gallery_container in gallery_containers:
                if get_text_from_container:
                    gallery_link = gallery_container.get_text()
                else:
                    gallery_url_container = gallery_container.find(
                        link_tag,
                        **{link_attribute_name: re.compile(link_attribute_value)}
                    )
                    if gallery_url_container.has_attr(url_attribute_name):
                        gallery_link = gallery_url_container[url_attribute_name]
                    else:
                        continue

                gallery_gids.append(gallery_link[1:])

            if not gallery_gids:
                # ext_logger.error('Server response: {}'.format(response.text))
                ext_logger.error('Got to page {}, but could not parse the response into galleries, stopping'.format(
                    query_values['page']))
                break

            # Listen to what the server says

            used = Gallery.objects.filter(gid__in=gallery_gids, provider=constants.provider_name)

            # If the amount of galleries present in database is equal to what we get from the page,
            # we assume we already processed everything. You can force to process everything by using:
            force_process, force_created = attrs.get_or_create(
                provider=provider,
                name='force_process',
                data_type='bool',
                defaults={
                    'value_bool': False,
                }
            )

            ext_logger.info(
                'Page has {} galleries, from which {} are already present in the database.'.format(
                    len(gallery_gids),
                    used.count()
                )
            )

            if not force_process.value and used.count() == len(gallery_gids):
                ext_logger.info(
                    'Got to page {}, it has already been processed entirely, stopping'.format(query_values['page']))
                break

            used_gids = used.values_list('gid', flat=True)

            for gallery_gid in gallery_gids:
                if gallery_gid not in used_gids:
                    gallery_link = urllib.parse.urljoin(constants.main_url, "/" + gallery_gid)

                    gallery_links.append(gallery_link)

            api_galleries = parser.fetch_multiple_gallery_data(gallery_links)

            if not api_galleries:
                # ext_logger.error('Server response: {}'.format(response.text))
                ext_logger.error(
                    'Got to page {}, but could not parse the gallery link into GalleryData instances'.format(
                        query_values['page'])
                )
                break

            for gallery_data in api_galleries:
                if gallery_data.gid not in used_gids:
                    if not gallery_data.dl_type:
                        gallery_data.dl_type = 'auto_wanted'
                    gallery_data.reason = attrs.fetch_value('wanted_reason_{}'.format(query_name)) or 'backup'
                    gallery = Gallery.objects.add_from_values(gallery_data)
                    # We match anyways in case there's a previous WantedGallery.
                    # Actually, we don't match since we only get metadata here, so it should not count as found.
                    publisher_name = ''
                    publisher = gallery.tags.filter(scope='publisher').first()
                    if publisher:
                        publisher_name = publisher.name

                    search_title = format_title_to_wanted_search(gallery.title)

                    wanted_galleries = WantedGallery.objects.filter(
                        title=gallery.title, search_title=search_title
                    )

                    if not wanted_galleries:
                        wanted_gallery = WantedGallery.objects.create(
                            title=gallery.title,
                            title_jpn=gallery.title_jpn,
                            search_title=search_title,
                            book_type=gallery.category,
                            page_count=gallery.filecount,
                            publisher=publisher_name,
                            add_as_hidden=True,
                            reason=attrs.fetch_value('wanted_reason_{}'.format(query_name)) or '',
                            public=attrs.fetch_value('wanted_public_{}'.format(query_name)) or False,
                            should_search=attrs.fetch_value('wanted_should_search_{}'.format(query_name)) or False,
                            keep_searching=attrs.fetch_value('wanted_keep_searching_{}'.format(query_name)) or False,
                            notify_when_found=attrs.fetch_value('wanted_notify_when_found_{}'.format(query_name)) or False,
                            provider=attrs.fetch_value('wanted_provider_{}'.format(query_name)) or '',
                            wanted_providers=attrs.fetch_value('wanted_providers_{}'.format(query_name)) or '',
                        )
                        for artist in gallery.tags.filter(scope='artist'):
                            artist_obj = Artist.objects.filter(name=artist.name).first()
                            if not artist_obj:
                                artist_obj = Artist.objects.create(name=artist.name)
                            wanted_gallery.artists.add(artist_obj)
                        ext_logger.info(
                            "Created wanted gallery ({}): {}, search title: {}".format(
                                wanted_gallery.book_type,
                                wanted_gallery.get_absolute_url(),
                                wanted_gallery.search_title
                            )
                        )

                        wanted_galleries = [wanted_gallery]

                    for wanted_gallery in wanted_galleries:

                        announce, announce_created = wanted_gallery.announces.get_or_create(
                            announce_date=gallery.create_date,
                            release_date=gallery.posted,
                            type='release_date',
                            source=constants.provider_name,
                        )
                        if announce_created and gallery.thumbnail:
                            announce.copy_img(gallery.thumbnail.path)
                            wanted_gallery.calculate_nearest_release_date()

            # galleries.extend(api_galleries)

            # API returns 25 max results per query, so if we get 24 or less, means there's no more pages.
            # API Manual says 25, but we get 50 results normally!
            if len(api_galleries) < 1:
                ext_logger.info(
                    'Got to page {}, and we got less than 1 gallery, '
                    'meaning there is no more pages, stopping'.format(query_values['page'])
                )
                break

            query_values['page'] += 1

    ext_logger.info("{} Auto wanted ended.".format(
        constants.provider_name
    ))
