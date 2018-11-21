'''<b>Save Croped Objects </b> Crops objects from an image and saves the croped
images.
<hr>
In order to process large images it can be benefitial to crop regions of
interest out. This module will crop out segmented images from an object and
save the cropped images as well as the masks used.
<p>You can choose from many different image formats for saving your files. This
allows you to use the module as a file format converter, by loading files
in their original format and then saving them in an alternate format.</p>

<p>Note that saving images in 12-bit format is not supported, and 16-bit format
is supported for TIFF only.</p>

See also <b>NamesAndTypes</b>, <b>ConserveMemory</b>.
'''

import logging
import os
import re
import sys
import traceback

import matplotlib
import numpy as np
import scipy.io.matlab.mio
import scipy.ndimage as ndi
logger = logging.getLogger(__name__)

import cellprofiler.module as cpm
import cellprofiler.measurement as cpmeas
import cellprofiler.setting as cps
from cellprofiler.setting import YES, NO
import cellprofiler.preferences as cpp
from cellprofiler.preferences import \
     standardize_default_folder_names, DEFAULT_INPUT_FOLDER_NAME, \
     DEFAULT_OUTPUT_FOLDER_NAME, ABSOLUTE_FOLDER_NAME, \
     DEFAULT_INPUT_SUBFOLDER_NAME, DEFAULT_OUTPUT_SUBFOLDER_NAME, \
     get_default_image_directory
#from cellprofiler.utilities.relpath import relpath
from cellprofiler.modules.loadimages import C_FILE_NAME, C_PATH_NAME, C_URL
from cellprofiler.modules.loadimages import \
     C_OBJECTS_FILE_NAME, C_OBJECTS_PATH_NAME, C_OBJECTS_URL
from cellprofiler.modules.loadimages import pathname2url
from centrosome.cpmorphology import distance_color_labels
from bioformats.formatwriter import write_image
import bioformats.omexml as ome

import tifffile

NOTDEFINEDYET = 'Helptext Not Defined Yet'
USING_METADATA_TAGS_REF = NOTDEFINEDYET
USING_METADATA_HELP_REF = NOTDEFINEDYET
IO_FOLDER_CHOICE_HELP_TEXT = NOTDEFINEDYET
IO_WITH_METADATA_HELP_TEXT = NOTDEFINEDYET

IF_IMAGE       = "Image"
IF_MASK        = "Mask"
IF_CROPPING    = "Cropping"
IF_FIGURE      = "Module window"
IF_MOVIE       = "Movie"
IF_OBJECTS     = "Objects"
IF_ALL = [IF_IMAGE, IF_MASK, IF_CROPPING, IF_MOVIE, IF_OBJECTS]

OLD_BIT_DEPTH_8 = "8"
OLD_BIT_DEPTH_16 = "16"
BIT_DEPTH_8 = "8-bit integer"
BIT_DEPTH_16 = "16-bit integer"
BIT_DEPTH_FLOAT = "32-bit floating point"

FN_FROM_IMAGE  = "From image filename"
FN_SEQUENTIAL  = "Sequential numbers"
FN_SINGLE_NAME = "Single name"
SINGLE_NAME_TEXT = "Enter single file name"
FN_WITH_METADATA = "Name with metadata"
FN_IMAGE_FILENAME_WITH_METADATA = "Image filename with metadata"
METADATA_NAME_TEXT = ("""Enter file name with metadata""")
SEQUENTIAL_NUMBER_TEXT = "Enter file prefix"
FF_BMP         = "bmp"
FF_JPG         = "jpg"
FF_JPEG        = "jpeg"
FF_PBM         = "pbm"
FF_PCX         = "pcx"
FF_PGM         = "pgm"
FF_PNG         = "png"
FF_PNM         = "pnm"
FF_PPM         = "ppm"
FF_RAS         = "ras"
FF_TIF         = "tif"
FF_TIFF        = "tiff"
FF_XWD         = "xwd"
FF_AVI         = "avi"
FF_MAT         = "mat"
FF_MOV         = "mov"
FF_SUPPORTING_16_BIT = [FF_TIF, FF_TIFF]
PC_WITH_IMAGE  = "Same folder as image"
OLD_PC_WITH_IMAGE_VALUES = ["Same folder as image"]
PC_CUSTOM      = "Custom"
PC_WITH_METADATA = "Custom with metadata"
WS_EVERY_CYCLE = "Every cycle"
WS_FIRST_CYCLE = "First cycle"
WS_LAST_CYCLE  = "Last cycle"
CM_GRAY        = "gray"

GC_GRAYSCALE = "Grayscale"
GC_COLOR = "Color"

'''Offset to the directory path setting'''
OFFSET_DIRECTORY_PATH = 11

'''Offset to the bit depth setting in version 11'''
OFFSET_BIT_DEPTH_V11 = 12

class SaveObjectCrops(cpm.Module):

    module_name = "SaveObjectCrops"
    variable_revision_number = 2
    category = "File Processing"

    def create_settings(self):
        self.input_type = cps.Choice(
            "Select the type of input",
            [IF_IMAGE], IF_IMAGE)

        self.image_name  = cps.ImageNameSubscriber(
            "Select the image to save",cps.NONE, doc = """
            <i>(Used only if "%(IF_IMAGE)s", "%(IF_MASK)s" or "%(IF_CROPPING)s" are selected to save)</i><br>
            Select the image you want to save."""%globals())

        self.input_object_name = cps.ObjectNameSubscriber(
            "Select the objects to save", cps.NONE)

        self.objects_name = cps.ObjectNameSubscriber(
            "Select the objects to crop and save", cps.NONE,doc = """
            Select the objects that you want to save."""%globals())

        self.file_name_method = cps.Choice(
            "Select method for constructing file names",
            [FN_FROM_IMAGE,
             ], doc="""
            Several choices are available for constructing the image file name:
            <ul>
            <li><i>%(FN_FROM_IMAGE)s:</i> The filename will be constructed based
            on the original filename of an input image specified in <b>NamesAndTypes</b>.
            You will have the opportunity to prefix or append
            additional text.
            <p>If you have metadata associated with your images, you can append an text
            to the image filename using a metadata tag. This is especially useful if you
            want your output given a unique label according to the metadata corresponding
            to an image group. The name of the metadata to substitute can be provided for
            each image for each cycle using the <b>Metadata</b> module.
            %(USING_METADATA_TAGS_REF)s%(USING_METADATA_HELP_REF)s.</p></li>
            </ul>"""%globals())

        self.file_image_name = cps.FileImageNameSubscriber(
            "Select image name for file prefix",
            cps.NONE,doc="""
            <i>(Used only when "%(FN_FROM_IMAGE)s" is selected for contructing the filename)</i><br>
            Select an image loaded using <b>NamesAndTypes</b>. The original filename will be
            used as the prefix for the output filename."""%globals())


        self.wants_file_name_suffix = cps.Binary(
            "Append a suffix to the image file name?", False, doc = """
            Select <i>%(YES)s</i> to add a suffix to the image's file name.
            Select <i>%(NO)s</i> to use the image name as-is."""%globals())

        self.file_name_suffix = cps.Text(
            "Text to append to the image name",
            "", metadata = True, doc="""
            <i>(Used only when constructing the filename from the image filename)</i><br>
            Enter the text that should be appended to the filename specified above.""")

        self.file_format = cps.Choice(
            "Saved file format",
            [FF_TIFF],
            value = FF_TIFF, doc="""
            <i>(Used only when saving non-movie files)</i><br>
            Select the image or movie format to save the image(s). Most common
            image formats are available; MAT-files are readable by MATLAB.""")


        self.pathname = SaveImagesDirectoryPath(
            "Output file location", self.file_image_name,doc = """
            <i>(Used only when saving non-movie files)</i><br>
            This setting lets you choose the folder for the output
            files. %(IO_FOLDER_CHOICE_HELP_TEXT)s
            <p>An additional option is the following:
            <ul>
            <li><i>Same folder as image</i>: Place the output file in the same folder
            that the source image is located.</li>
            </ul></p>
            <p>%(IO_WITH_METADATA_HELP_TEXT)s %(USING_METADATA_TAGS_REF)s.
            For instance, if you have a metadata tag named
            "Plate", you can create a per-plate folder by selecting one the subfolder options
            and then specifying the subfolder name as "\g&lt;Plate&gt;". The module will
            substitute the metadata values for the current image set for any metadata tags in the
            folder name.%(USING_METADATA_HELP_REF)s.</p>
            <p>If the subfolder does not exist when the pipeline is run, CellProfiler will
            create it.</p>
            <p>If you are creating nested subfolders using the sub-folder options, you can
            specify the additional folders separated with slashes. For example, "Outlines/Plate1" will create
            a "Plate1" folder in the "Outlines" folder, which in turn is under the Default
            Input/Output Folder. The use of a forward slash ("/") as a folder separator will
            avoid ambiguity between the various operating systems.</p>"""%globals())

        self.bit_depth = cps.Choice(
            "Image bit depth",
            [BIT_DEPTH_8, BIT_DEPTH_16, BIT_DEPTH_FLOAT],doc="""
            <i>(Used only when saving files in a non-MAT format)</i><br>
            Select the bit-depth at which you want to save the images.
            <i>%(BIT_DEPTH_FLOAT)s</i> saves the image as floating-point decimals
            with 32-bit precision in its raw form, typically scaled between
            0 and 1.
            <b>%(BIT_DEPTH_16)s and %(BIT_DEPTH_FLOAT)s images are supported only
            for TIF formats. Currently, saving images in 12-bit is not supported.</b>""" %
            globals())

        self.object_extension = cps.Integer("Object extension", value=1, doc="""
            How many pixels should the bounding box of the objects be extended
                                            before cropping""")

        self.overwrite = cps.Binary(
            "Overwrite existing files without warning?",False,doc="""
            Select <i>%(YES)s</i> to automatically overwrite a file if it already exists.
            Select <i>%(NO)s</i> to be prompted for confirmation first.
            <p>If you are running the pipeline on a computing cluster,
            select <i>%(YES)s</i> since you will not be able to intervene and answer the confirmation prompt.</p>"""%globals())

        self.when_to_save = cps.Choice(
            "When to save",
            [WS_FIRST_CYCLE],
            doc="""<a name='when_to_save'>
            <i>(Used only when saving non-movie files)</i><br>
            Specify at what point during pipeline execution to save file(s). </a>
            <ul>
            <li><i>%(WS_EVERY_CYCLE)s:</i> Useful for when the image of interest is created every cycle and is
            not dependent on results from a prior cycle.</li>
            </ul> """%globals())


        self.update_file_names = cps.Binary(
            "Record the file and path information to the saved image?",False,doc="""
            Select <i>%(YES)s</i> to store filename and pathname data for each of the new files created
            via this module as a per-image measurement.
            <p>Instances in which this information may be useful include:
            <ul>
            <li>Exporting measurements to a database, allowing
            access to the saved image. If you are using the machine-learning tools or image
            viewer in CellProfiler Analyst, for example, you will want to enable this setting if you want
            the saved images to be displayed along with the original images.</li>
            <li>Allowing downstream modules (e.g., <b>CreateWebPage</b>) to access
            the newly saved files.</li>
            </ul></p>"""%globals())

        self.create_subdirectories = cps.Binary(
            "Create subfolders in the output folder?",False,doc = """
            Select <i>%(YES)s</i> to create subfolders to match the input image folder structure."""%globals())

        self.root_dir = cps.DirectoryPath(
            "Base image folder", doc = """
            <i>Used only if creating subfolders in the output folder</i>
            In subfolder mode, <b>SaveImages</b> determines the folder for
            an image file by examining the path of the matching input file.
            The path that SaveImages uses is relative to the image folder
            chosen using this setting. As an example, input images might be stored
            in a folder structure of "images%(sep)s<i>experiment-name</i>%(sep)s
            <i>date</i>%(sep)s<i>plate-name</i>". If the image folder is
            "images", <b>SaveImages</b> will store images in the subfolder,
            "<i>experiment-name</i>%(sep)s<i>date</i>%(sep)s<i>plate-name</i>".
            If the image folder is "images%(sep)s<i>experiment-name</i>",
            <b>SaveImages</b> will store images in the subfolder,
            <i>date</i>%(sep)s<i>plate-name</i>".
            """ % dict(sep=os.path.sep))

    def settings(self):
        """Return the settings in the order to use when saving"""
        return [self.input_type,
                self.input_object_name,
                self.image_name,
                self.objects_name, self.object_extension,
                self.file_name_method, self.file_image_name,
                self.wants_file_name_suffix,
                self.file_name_suffix, self.file_format,
                self.pathname, self.bit_depth,
                self.overwrite, self.when_to_save,
                self.update_file_names, self.create_subdirectories,
                self.root_dir
                ]

    def visible_settings(self):
        """Return only the settings that should be shown"""
        result = []
        result.append(self.input_type)
        if self.input_type.value == IF_IMAGE:
            result.append(self.image_name)
        else:
            result.append(self.input_object_name)
        result.append(self.objects_name)
        result.append(self.object_extension),
        result.append(self.file_name_method)
        if self.file_name_method == FN_FROM_IMAGE:
            result += [self.file_image_name, self.wants_file_name_suffix]
            if self.wants_file_name_suffix:
                result.append(self.file_name_suffix)
        else:
            raise NotImplementedError("Unhandled file name method: %s"%(self.file_name_method))
        result.append(self.file_format)
        result.append(self.pathname)
        result.append(self.overwrite)
        result.append(self.update_file_names)
        if self.file_name_method == FN_FROM_IMAGE:
            result.append(self.create_subdirectories)
            if self.create_subdirectories:
                result.append(self.root_dir)
        return result

    @property
    def module_key(self):
        return "%s_%d"%(self.module_name, self.module_num)

    def prepare_group(self, workspace, grouping, image_numbers):
        return True

    def prepare_to_create_batch(self, workspace, fn_alter_path):
        self.pathname.alter_for_create_batch_files(fn_alter_path)
        if self.create_subdirectories:
            self.root_dir.alter_for_create_batch_files(fn_alter_path)

    def run(self,workspace):
        """Run the module

        pipeline     - instance of CellProfiler.Pipeline for this run
        workspace    - the workspace contains:
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - display within this frame (or None to not display)
        """
        should_save = self.run_crops(workspace)
        workspace.display_data.filename = self.get_filename(
            workspace, make_dirs = False, check_overwrite = False)

    def display(self, workspace, figure):
        if self.show_window:
            figure.set_subplots((1, 1))
            outcome = ("Wrote %s" if workspace.display_data.wrote_image
                       else "Did not write %s")
            figure.subplot_table(0, 0, [[outcome %
                                         (workspace.display_data.filename)]])


    def run_crops(self,workspace):
        """Handle cropping of an image by objects"""
        #
        # First, check to see if we should save this image
        #
        self.save_crops(workspace)
        return True

    def _extend_slice(self, sl, extent, dim_max, dim_min=0):
        """
        helper function to extend single slices
        :param sl: numpy slice
        :param extent: how many pixels should be extended
        :param dim_max: maximum coordinate in dimension
        :param dim_min: minimum coordinate in dimension, e.g. 0
        :return: the new extended slice
        """

        x_start = max(sl.start-extent,dim_min)
        x_end = min(sl.stop+ extent, dim_max)
        return np.s_[x_start:x_end]

    def _extend_slice_touple(self, slice_touple, extent, max_dim ,min_dim =(0,0)):
        """
        Helper for save_crops
        Extends a numpy slice touple, e.g. corresponding to a bounding box
        :param slice_touple: a numpy slice
        :param extent: amount of extension in pixels
        :param max_dim: maximum image coordinates (e.g. from img.shape)
        :param min_dim: minimum image coordinates, usually (0,0)
        :return: an extended numpy slice

        """
        new_slice = tuple(self._extend_slice(s,extent, d_max, d_min) for s, d_max, d_min in
              zip(slice_touple, max_dim, min_dim))

        return new_slice

    def _save_object_stack(self, folder, basename, img_stack, slices, labels=None):
        """
        Saves slices from an image stack as.
        :param folder: The folder to save it in
        :param basename: The filename
        :param img_stack: the image stack. should be CXY
        :param slices: a list of numpy slices sphecifying the regions to be saved
        :return:
        """
        if labels is None:
            labels = range(slices)
        for lab, sl in zip(labels, slices):
            if sl is None:
                pass
            x = sl[0].start
            y = sl[1].start

            exsl = tuple([np.s_[:]]+[s for s in sl])

            fn = os.path.join(folder, basename + '_l' + str(lab + 1) + '_x' + str(x) + '_y' + str(y)+'.tiff')

            with tifffile.TiffWriter(fn, imagej=True) as tif:
                timg = img_stack[exsl]
                for chan in range(timg.shape[0]):
                    tif.save(timg[chan, :, :].squeeze())

    def save_crops(self, workspace):
        """ Crops the image by objects """
        objects_name = self.objects_name.value
        objects = workspace.object_set.get_objects(objects_name)
        if self.input_type == IF_IMAGE:
            image_name = self.image_name.value
            image = workspace.image_set.get_image(image_name)
            pixels = image.pixel_data
        elif self.input_type == IF_OBJECTS:
            obj_name = self.input_object_name.value
            inp_obj = workspace.object_set.get_objects(obj_name)
            pixels = inp_obj.get_segmented()
        else:
            raise('invalid choice of input')

        filename = self.get_filename(workspace)
        object_extension = self.object_extension.value
        if filename is None:  # failed overwrite check
            return

        slices = ndi.find_objects(objects.segmented)
        slices, labels = zip(*[(s, label) for label, s  in
                               enumerate(slices) if s is not None])

        ext_slices = [self._extend_slice_touple(sl, object_extension,
                                              [pixels.shape[0], pixels.shape[1]]) for sl in slices]
        out_folder = os.path.dirname(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        #  the stack for imctools needs to be cxy, while it is xyc in cp
        if len(pixels.shape) == 2:
            stack = pixels.reshape([1]+list(pixels.shape))
        else:
            stack = np.rollaxis(pixels,2,0)

        # fix the dtype
        if stack.dtype == np.int8:
            stack = stack.astype(np.uint8)
        elif stack.dtype == np.int16:
            stack = stack.astype(np.uint16)
        elif stack.dtype == np.float:
            stack = stack.astype(np.float32)
        elif stack.dtype == np.int32:
            stack = stack.astype(np.uint16)

        self._save_object_stack(out_folder, basename, stack, ext_slices,
                              labels)
        self.save_filename_measurements(workspace)
        if self.show_window:
            workspace.display_data.wrote_image = True

    def post_group(self, workspace, *args):
        pass

    def check_overwrite(self, filename, workspace):
        '''Check to see if it's legal to overwrite a file

        Throws an exception if can't overwrite and no interaction available.
        Returns False if can't overwrite, otherwise True.
        '''
        if not self.overwrite.value and os.path.isfile(filename):
            try:
                return (workspace.interaction_request(self, workspace.measurements.image_set_number, filename) == "Yes")
            except workspace.NoInteractionException:
                raise ValueError('SaveImages: trying to overwrite %s in headless mode, but Overwrite files is set to "No"' % (filename))
        return True

    def handle_interaction(self, image_set_number, filename):
        '''handle an interaction request from check_overwrite()'''
        import wx
        dlg = wx.MessageDialog(wx.GetApp().TopWindow,
                               "%s #%d, set #%d - Do you want to overwrite %s?" % \
                                   (self.module_name, self.module_num, image_set_number, filename),
                               "Warning: overwriting file", wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal() == wx.ID_YES
        return "Yes" if result else "No"

    def save_filename_measurements(self, workspace):
        if self.update_file_names.value:
            filename = self.get_filename(workspace, make_dirs = False,
                                         check_overwrite = False)
            pn, fn = os.path.split(filename)
            url = pathname2url(filename)
            workspace.measurements.add_measurement(cpmeas.IMAGE,
                                                   self.file_name_feature,
                                                   fn,
                                                   can_overwrite=True)
            workspace.measurements.add_measurement(cpmeas.IMAGE,
                                                   self.path_name_feature,
                                                   pn,
                                                   can_overwrite=True)
            workspace.measurements.add_measurement(cpmeas.IMAGE,
                                                   self.url_feature,
                                                   url,
                                                   can_overwrite=True)

    @property
    def file_name_feature(self):
        '''The file name measurement for the output file'''
        #if self.save_image_or_figure == IF_OBJECTS:
        #    return '_'.join((C_OBJECTS_FILE_NAME, self.objects_name.value))
        return '_'.join((C_FILE_NAME, self.image_name.value))

    @property
    def path_name_feature(self):
        '''The path name measurement for the output file'''
        # if self.save_image_or_figure == IF_OBJECTS:
        #    return '_'.join((C_OBJECTS_PATH_NAME, self.objects_name.value))
        return '_'.join((C_PATH_NAME, self.image_name.value))

    @property
    def url_feature(self):
        '''The URL measurement for the output file'''
        #if self.save_image_or_figure == IF_OBJECTS:
        #    return '_'.join((C_OBJECTS_URL, self.objects_name.value))
        return '_'.join((C_URL, self.image_name.value))

    @property
    def source_file_name_feature(self):
        '''The file name measurement for the exemplar disk image'''
        return '_'.join((C_FILE_NAME, self.file_image_name.value))

    def source_path(self, workspace):
        '''The path for the image data, or its first parent with a path'''
        if self.file_name_method.value == FN_FROM_IMAGE:
            path_feature = '%s_%s' % (C_PATH_NAME, self.file_image_name.value)
            assert workspace.measurements.has_feature(cpmeas.IMAGE, path_feature),\
                "Image %s does not have a path!" % (self.file_image_name.value)
            return workspace.measurements.get_current_image_measurement(path_feature)

        # ... otherwise, chase the cpimage hierarchy looking for an image with a path
        cur_image = workspace.image_set.get_image(self.image_name.value)
        while cur_image.path_name is None:
            cur_image = cur_image.parent_image
            assert cur_image is not None, "Could not determine source path for image %s' % (self.image_name.value)"
        return cur_image.path_name

    def get_measurement_columns(self, pipeline):
        if self.update_file_names.value:
            return [(cpmeas.IMAGE,
                     self.file_name_feature,
                     cpmeas.COLTYPE_VARCHAR_FILE_NAME),
                    (cpmeas.IMAGE,
                     self.path_name_feature,
                     cpmeas.COLTYPE_VARCHAR_PATH_NAME)]
        else:
            return []

    def get_filename(self, workspace, make_dirs=True, check_overwrite=True):
        "Concoct a filename for the current image based on the user settings"

        measurements=workspace.measurements
        file_name_feature = self.source_file_name_feature
        filename = measurements.get_current_measurement('Image',
                                                        file_name_feature)
        filename = os.path.splitext(filename)[0]
        if self.wants_file_name_suffix:
            suffix = self.file_name_suffix.value
            suffix = workspace.measurements.apply_metadata(suffix)
            filename += suffix

        filename = "%s.%s"%(filename,self.get_file_format())
        pathname = self.pathname.get_absolute_path(measurements)
        if self.create_subdirectories:
            image_path = self.source_path(workspace)
            subdir = os.path.relpath(image_path, self.root_dir.get_absolute_path())
            pathname = os.path.join(pathname, subdir)
        if len(pathname) and not os.path.isdir(pathname) and make_dirs:
            try:
                os.makedirs(pathname)
            except:
                #
                # On cluster, this can fail if the path was created by
                # another process after this process found it did not exist.
                #
                if not os.path.isdir(pathname):
                    raise
        result = os.path.join(pathname, filename)
        if check_overwrite and not self.check_overwrite(result, workspace):
            return

        if check_overwrite and os.path.isfile(result):
            try:
                os.remove(result)
            except:
                import bioformats
                bioformats.clear_image_reader_cache()
                os.remove(result)
        return result

    def get_file_format(self):
        """Return the file format associated with the extension in self.file_format
        """
        #if self.save_image_or_figure == IF_MOVIE:
        #    return self.movie_format.value
        return self.file_format.value

    def get_bit_depth(self):
        if (self.save_image_or_figure == IF_IMAGE and
            self.get_file_format() in FF_SUPPORTING_16_BIT):
            return self.bit_depth.value
        else:
            return BIT_DEPTH_8

    def upgrade_settings(self, setting_values, variable_revision_number,
                         module_name, from_matlab):
        """Adjust the setting values to be backwards-compatible with old versions

        """
        if variable_revision_number < 2:
            setting_values = [IF_IMAGE, cps.NONE] + setting_values
        return setting_values, variable_revision_number, from_matlab

    def validate_module(self, pipeline):
        #if (self.save_image_or_figure in (IF_IMAGE, IF_MASK, IF_CROPPING) and
        #    self.when_to_save in (WS_FIRST_CYCLE, WS_EVERY_CYCLE)):
            #
            # Make sure that the image name is available on every cycle
            #
        #    for setting in cps.get_name_providers(pipeline,
        #                                          self.image_name):
        #        if setting.provided_attributes.get(cps.AVAILABLE_ON_LAST_ATTRIBUTE):
                    #
                    # If we fell through, then you can only save on the last cycle
                    #
        #            raise cps.ValidationError("%s is only available after processing all images in an image group" %
        #                                      self.image_name.value,
        #                                      self.when_to_save)

        # XXX - should check that if file_name_method is
        # FN_FROM_IMAGE, that the named image actually has the
        # required path measurement

        # Make sure metadata tags exist
        pass

class SaveImagesDirectoryPath(cps.DirectoryPath):
    '''A specialized version of DirectoryPath to handle saving in the image dir'''

    def __init__(self, text, file_image_name, doc):
        '''Constructor
        text - explanatory text to display
        file_image_name - the file_image_name setting so we can save in same dir
        doc - documentation for user
        '''
        super(SaveImagesDirectoryPath, self).__init__(
            text, dir_choices = [
                cps.DEFAULT_OUTPUT_FOLDER_NAME, cps.DEFAULT_INPUT_FOLDER_NAME,
                PC_WITH_IMAGE, cps.ABSOLUTE_FOLDER_NAME,
                cps.DEFAULT_OUTPUT_SUBFOLDER_NAME,
                cps.DEFAULT_INPUT_SUBFOLDER_NAME], doc=doc)
        self.file_image_name = file_image_name

    def get_absolute_path(self, measurements=None, image_set_index=None):
        if self.dir_choice == PC_WITH_IMAGE:
            path_name_feature = "PathName_%s" % self.file_image_name.value
            return measurements.get_current_image_measurement(path_name_feature)
        return super(SaveImagesDirectoryPath, self).get_absolute_path(
            measurements, image_set_index)

    def test_valid(self, pipeline):
        if self.dir_choice not in self.dir_choices:
            raise cps.ValidationError("%s is not a valid directory option" %
                                      self.dir_choice, self)

    @staticmethod
    def upgrade_setting(value):
        '''Upgrade setting from previous version'''
        dir_choice, custom_path = cps.DirectoryPath.split_string(value)
        if dir_choice in OLD_PC_WITH_IMAGE_VALUES:
            dir_choice = PC_WITH_IMAGE
        elif dir_choice in (PC_CUSTOM, PC_WITH_METADATA):
            if custom_path.startswith('.'):
                dir_choice = cps.DEFAULT_OUTPUT_SUBFOLDER_NAME
            elif custom_path.startswith('&'):
                dir_choice = cps.DEFAULT_INPUT_SUBFOLDER_NAME
                custom_path = '.' + custom_path[1:]
            else:
                dir_choice = cps.ABSOLUTE_FOLDER_NAME
        else:
            return cps.DirectoryPath.upgrade_setting(value)
        return cps.DirectoryPath.static_join_string(dir_choice, custom_path)

def save_bmp(path, img):
    '''Save an image as a Microsoft .bmp file

    path - path to file to save

    img - either a 2d, uint8 image or a 2d + 3 plane uint8 RGB color image

    Saves file as an uncompressed 8-bit or 24-bit .bmp image
    '''
    #
    # Details from
    # http://en.wikipedia.org/wiki/BMP_file_format#cite_note-DIBHeaderTypes-3
    #
    # BITMAPFILEHEADER
    # http://msdn.microsoft.com/en-us/library/dd183374(v=vs.85).aspx
    #
    # BITMAPINFOHEADER
    # http://msdn.microsoft.com/en-us/library/dd183376(v=vs.85).aspx
    #
    BITMAPINFOHEADER_SIZE = 40
    img = img.astype(np.uint8)
    w = img.shape[1]
    h = img.shape[0]
    #
    # Convert RGB to interleaved
    #
    if img.ndim == 3:
        rgb = True
        #
        # Compute padded raster length
        #
        raster_length = (w * 3 + 3) & ~ 3
        tmp = np.zeros((h, raster_length), np.uint8)
        #
        # Do not understand why but RGB is BGR
        #
        tmp[:, 2:(w*3):3] = img[:, :, 0]
        tmp[:, 1:(w*3):3] = img[:, :, 1]
        tmp[:, 0:(w*3):3] = img[:, :, 2]
        img = tmp
    else:
        rgb = False
        if w % 4 != 0:
            raster_length = (w + 3) & ~ 3
            tmp = np.zeros((h, raster_length), np.uint8)
            tmp[:, :w] = img
            img = tmp
    #
    # The image is upside-down in .BMP
    #
    bmp = np.ascontiguousarray(np.flipud(img)).data
    with open(path, "wb") as fd:
        def write2(value):
            '''write a two-byte little-endian value to the file'''
            fd.write(np.array([value], "<u2").data[:2])
        def write4(value):
            '''write a four-byte little-endian value to the file'''
            fd.write(np.array([value], "<u4").data[:4])
        #
        # Bitmap file header (1st pass)
        # byte
        # 0-1 = "BM"
        # 2-5 = length of file
        # 6-9 = 0
        # 10-13 = offset from beginning of file to bitmap bits
        fd.write("BM")
        length = 14 # BITMAPFILEHEADER
        length += BITMAPINFOHEADER_SIZE
        if not rgb:
            length += 4 * 256         # 256 color table entries
        hdr_length = length
        length += len(bmp)
        write4(length)
        write4(0)
        write4(hdr_length)
        #
        # BITMAPINFOHEADER
        #
        write4(BITMAPINFOHEADER_SIZE) # biSize
        write4(w)                     # biWidth
        write4(h)                     # biHeight
        write2(1)                     # biPlanes = 1
        write2(24 if rgb else 8)      # biBitCount
        write4(0)                     # biCompression = BI_RGB
        write4(len(bmp))              # biSizeImage
        write4(7200)                  # biXPelsPerMeter
        write4(7200)                  # biYPelsPerMeter
        write4(0 if rgb else 256)     # biClrUsed (no palette)
        write4(0)                     # biClrImportant
        if not rgb:
            # The color table
            color_table = np.column_stack(
                [np.arange(256)]* 3 +
                [np.zeros(256, np.uint32)]).astype(np.uint8)
            fd.write(np.ascontiguousarray(color_table, np.uint8).data)
        fd.write(bmp)
