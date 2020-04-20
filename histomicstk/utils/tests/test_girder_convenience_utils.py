# -*- coding: utf-8 -*-
import pytest
import os
import sys
thisDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(thisDir, '../../../'))

# import tests.htk_test_utilities as utilities  # noqa
from tests.htk_test_utilities import girderClient  # noqa
from histomicstk.utils.girder_convenience_utils import \
    get_absolute_girder_folderpath, \
    update_styles_for_annotations_in_slide, \
    revert_annotations_in_slide, \
    update_permissions_for_annotations_in_slide  # noqa


# # for protyping
# from tests.htk_test_utilities import _connect_to_existing_local_dsa
# girderClient = _connect_to_existing_local_dsa()

global gc, iteminfo, posted_folder


class TestGirderConvenience(object):
    """Test utilities for interaction with girder."""

    # pytest runs tests in the order they appear in the module
    @pytest.mark.usefixtures('girderClient')  # noqa
    def test_prep(self, girderClient):  # noqa
        global gc, iteminfo, posted_folder

        gc = girderClient

        # get original item
        original_iteminfo = gc.get('/item', parameters={
            'text': "TCGA-A2-A0YE-01Z-00-DX1"})[0]

        # create a sample folder
        posted_folder = gc.post(
            '/folder', data={
                'parentId': original_iteminfo['folderId'],
                'name': 'test'
            })

        # copy the item so that everythign we do here does not affect
        # other unit tests that use that item
        iteminfo = gc.post(
            "/item/%s/copy" % original_iteminfo['_id'], data={
                'name': 'test_slide_gcutils',
                'copyAnnotations': True,
            })

    def test_get_absolute_girder_path(self):
        # now get and check absolute path
        fpath = get_absolute_girder_folderpath(
            gc=gc, folder_info=posted_folder)
        assert fpath == 'Public/test/'

    def test_update_permissions_for_annotations_in_slide(self):
        admininfo = gc.get('/user', parameters={
            'text': "admin"})[0]

        # params to pass to update_permissions_for_annotation()
        update_params = {
            'users_to_add': [
                {'level': 2, 'id': admininfo['_id'],
                 'login': admininfo['login']},
            ],
            'groups_to_add': [],
            'replace_original_groups': True,
            'replace_original_users': True,
        }
        resps = update_permissions_for_annotations_in_slide(
            gc=gc, slide_id=iteminfo['_id'],
            # monitorPrefix='test_update_permissions_for_annotations_in_slide',
            **update_params
        )
        assert len(resps) == 8
        assert resps[0]['access']['users'] == [
            {'flags': [], 'id': admininfo['_id'], 'level': 2}
        ]
        assert resps[0]['access']['groups'] == []

    def test_update_styles_for_annotations_in_slide(self):
        resps = update_styles_for_annotations_in_slide(
            gc=gc, slide_id=iteminfo['_id'],
            changes={
                'roi': {
                    'group': 'modified_roi',
                    'lineColor': 'rgb(0,0,255)',
                    'fillColor': 'rgba(0,0,255,0.3)',
                },
            },
            # monitorPrefix='test_update_styles_for_annotations_in_slide',
        )
        modified = [j for j in resps if j is not None]
        assert len(modified) == 3
        assert "modified_roi" in modified[0]['groups']

    def test_revert_annotations_in_slide(self):
        # delete elements for one annotation
        anns = gc.get('/annotation/item/%s' % iteminfo['_id'])
        anns[0]['annotation']['elements'] = []
        _ = gc.put(
            "/annotation/%s" % anns[0]['_id'], json=anns[0]['annotation'])

        # now revert
        resps = revert_annotations_in_slide(
            gc=gc, slide_id=iteminfo['_id'],
            revert_to_nonempty_elements=False,
            only_revert_if_empty=False,
            # monitorPrefix='test_revert_annotations_in_slide',
        )
        modified = [j for j in resps if len(j) > 0]
        assert len(modified) >= 1
        ann = gc.get('/annotation/%s' % modified[0]['_id'])
        assert len(ann['annotation']['elements']) >= 1
