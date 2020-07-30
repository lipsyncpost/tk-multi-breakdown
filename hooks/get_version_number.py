# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()

# the template key we use to find the version number
VERSION_KEY = "version"


class GetVersionNumber(HookBaseClass):
    """
    Hook called to scan the disk and determine the highest version.
    Given a template and some fields, return the highest version number found on disk.
    The template key containing the version number is assumed to be named {version}.
    """

    def execute(self, template, curr_fields, **kwargs):
        """
        Main hook entry point.

        :param template: Template object to calculate for
        :param dict curr_fields: A complete set of fields for the template

        :returns: The highest version number found
        :rtype: int
        """
        self._app = self.parent
        highest_version = -1

        if template is not None:
            # calculate visibility
            # check if this is the latest item

            # note - have to do some tricks here to get sequences and stereo working
            # need to fix this in Tank platform

            # get all eyes, all frames and all versions
            # potentially a HUGE glob, so may be slow...
            # todo: better support for sequence iterations
            #       by using the abstract iteration methods

            # first, find all abstract (Sequence) keys from the template:
            abstract_keys = set()
            for key_name, key in template.keys.items():
                if key.is_abstract:
                    abstract_keys.add(key_name)

            # skip keys are all abstract keys + 'version' & 'eye' and 'camera_version' & 'Step' if a camera
            if "camera_version" in curr_fields:
                # set the version key
                VERSION_KEY = "camera_version"            
                skip_keys = [k for k in abstract_keys] + [VERSION_KEY, "eye", "version", "Step"]
            else:
                VERSION_KEY = "version"
                skip_keys = [k for k in abstract_keys] + [VERSION_KEY, "eye"]

            # then find all files, skipping these keys
            all_versions = self.sgtk.paths_from_template(
                template, curr_fields, skip_keys=skip_keys
            )

            # if we didn't find anything then something has gone wrong with our
            # logic as we should have at least one file so error out:
            # TODO - this should be handled more cleanly!
            if not all_versions:
                raise TankError("Failed to find any files!")

            # now look for the highest version number...
            highest_version = 0
            for ver in all_versions:
                curr_fields = template.get_fields(ver)
                if curr_fields[VERSION_KEY] > highest_version:
                    highest_version = curr_fields[VERSION_KEY]
        else:
            # we're getting the latest version directly from Shotgun using info Publish data
            if kwargs.get('sg_data') is not None:
                sg_data = kwargs.get('sg_data')

                sg_filter = [['project', 'is', sg_data['project']],
                            ['entity', 'is', sg_data['entity']],
                            ['task', 'is', sg_data['task']],
                            ['published_file_type', 'is', sg_data['published_file_type']],
                            ['name', 'is', sg_data['name']]
                            ]
                sg_fields = ['path', 'path_cache', 'entity', 'name', 'version_number']

                pf_list = self._app.shotgun.find('PublishedFile', sg_filter, sg_fields)

                # now look for the highest version number...
                if len(pf_list):
                    for p in pf_list:
                        version_number = p.get('version_number', -1)
                        if version_number > highest_version:
                            highest_version = version_number

        return highest_version
