import pyblish.api
import clique

from ayon_core.pipeline import OptionalPyblishPluginMixin


class CollectSequenceFrameData(
    pyblish.api.InstancePlugin,
    OptionalPyblishPluginMixin
):
    """Collect Original Sequence Frame Data

    If the representation includes files with frame numbers,
    then set `frameStart` and `frameEnd` for the instance to the
    start and end frame respectively
    """

    order = pyblish.api.CollectorOrder + 0.4905
    label = "Collect Original Sequence Frame Data"
    families = ["plate", "pointcache",
                "vdbcache", "online",
                "render"]
    hosts = ["traypublisher"]
    optional = True

    def process(self, instance):
        if not self.is_active(instance.data):
            return

        # editorial would fail since they might not be in database yet
        new_hierarchy = (
            instance.data.get("newHierarchyIntegration")
            # Backwards compatible (Deprecated since 24/06/06)
            or instance.data.get("newAssetPublishing")
        )
        if new_hierarchy:
            self.log.debug("Instance is creating new folders. Skipping.")
            return

        frame_data = self.get_frame_data_from_repre_sequence(instance)

        if not frame_data:
            # if no dict data skip collecting the frame range data
            return

        for key, value in frame_data.items():
            instance.data[key] = value
            self.log.debug(f"Collected Frame range data '{key}':{value} ")

    def get_frame_data_from_repre_sequence(self, instance):
        repres = instance.data.get("representations")

        entity: dict = (
            instance.data.get("taskEntity") or instance.data["folderEntity"]
        )
        entity_attributes: dict = entity["attrib"]

        if repres:
            first_repre = repres[0]
            if "ext" not in first_repre:
                self.log.warning("Cannot find file extension"
                                 " in representation data")
                return

            files = first_repre["files"]
            if not isinstance(files, list):
                files = [files]

            collections, _ = clique.assemble(files)
            if not collections:
                # No sequences detected and we can't retrieve
                # frame range
                self.log.debug(
                    "No sequences detected in the representation data."
                    " Skipping collecting frame range data.")
                return
            collection = collections[0]
            repres_frames = list(collection.indexes)

            return {
                "frameStart": repres_frames[0],
                "frameEnd": repres_frames[-1],
                "handleStart": 0,
                "handleEnd": 0,
                "fps": entity_attributes["fps"]
            }
