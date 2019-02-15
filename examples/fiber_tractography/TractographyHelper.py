from cmdint import CmdInterface
import numpy as np
from shutil import copyfile
from dipy.io import read_bvals_bvecs
import os

""" This exapmple contains two classes that help with fiber tractography using MITK Diffusion and MRtrix. It is only
intended as a larger example of multiple usages of CmdInterface and NOT (yet) as a polished class that wraps 
command line tools for fiber tractography and diffusion signal modelling.
"""


def flip_bvecs(input_dwi: str, output_dwi: str):
    bvals, bvecs = read_bvals_bvecs(input_dwi.replace('.nii.gz', '.bvals'), input_dwi.replace('.nii.gz', '.bvecs'))
    bvecs[:, 0] *= -1
    np.savetxt(output_dwi.replace('.nii.gz', '.bvecs'), np.transpose(bvecs), fmt='%10.6f')
    copyfile(input_dwi, output_dwi)
    copyfile(input_dwi.replace('.nii.gz', '.bvals'), output_dwi.replace('.nii.gz', '.bvals'))


class MitkTrackingHelper:

    def __init__(self):
        pass

    @staticmethod
    def recon_qball(input_dwi, out_folder, sh_order: int, do_flip_bvecs: bool):
        """ Perform analytical q-ball reconstruction with solid angle consideration and output the resulting
        spherical harmonics ODFs.
        """
        os.makedirs(out_folder, exist_ok=True)

        if do_flip_bvecs:
            flipper = CmdInterface(flip_bvecs)
            flipper.add_arg('input_dwi', input_dwi, check_input=True)
            input_dwi = input_dwi.replace(os.path.dirname(input_dwi), out_folder)
            input_dwi = input_dwi.replace('.nii.gz', '_flipped.nii.gz')
            flipper.add_arg('output_dwi', input_dwi, check_output=True)
            flipper.run()

        qball_recon = CmdInterface('MitkQballReconstruction')
        qball_recon.add_arg(key='-i', arg=input_dwi, check_input=True)
        qball_recon.add_arg(key='-o', arg=out_folder + 'odf_qball_mitk.nii.gz', check_output=True)
        qball_recon.add_arg(key='--sh_order', arg=sh_order)
        qball_recon.run()

        return out_folder + 'odf_qball_mitk.nii.gz'

    @staticmethod
    def recon_tensor(input_dwi: str, out_folder: str, do_flip_bvecs: bool = False):
        """ Perform diffusion tesnor modelling of the signal.
        """
        os.makedirs(out_folder, exist_ok=True)

        if do_flip_bvecs:
            flipper = CmdInterface(flip_bvecs)
            flipper.add_arg('input_dwi', input_dwi, check_input=True)
            input_dwi = input_dwi.replace(os.path.dirname(input_dwi), out_folder)
            input_dwi = input_dwi.replace('.nii.gz', '_flipped.nii.gz')
            flipper.add_arg('output_dwi', input_dwi, check_output=True)
            flipper.run()

        tensor_recon = CmdInterface('MitkTensorReconstruction')
        tensor_recon.add_arg(key='-i', arg=input_dwi, check_input=True)
        tensor_recon.add_arg(key='-o', arg=out_folder + 'tensors_mitk.dti', check_output=True)
        tensor_recon.run()

        return out_folder + 'tensors_mitk.dti'

    @staticmethod
    def train_rf(i: str,
                 t: str,
                 out_folder: str,
                 masks: str = None,
                 wm_masks: str = None,
                 volume_modification_images: str = None,
                 additional_feature_images: str = None,
                 num_trees: int = 30,
                 max_tree_depth: int = 25,
                 sample_fraction: float = 0.7,
                 use_sh_features: bool = 0,
                 sampling_distance: float = None,
                 max_wm_samples: int = None,
                 num_gm_samples: int = None):
        """
        Train a random forest for machine learning based tractography.

        i: input diffusion-weighted images
        t: input training tractograms
        o: output random forest (HDF5)
        masks: restrict training using a binary mask image (optional)
        wm_masks: if no binary white matter mask is specified
        volume_modification_images: specify a list of float images that modify the fiber density (optional)
        additional_feature_images: specify a list of float images that hold additional features (float) (optional)
        num_trees: number of trees (optional)
        max_tree_depth: maximum tree depth (optional)
        sample_fraction: fraction of samples used per tree (optional)
        use_sh_features: use SH features (optional)
        sampling_distance: resampling parameter for the input tractogram in mm (determines number of white-matter samples) (optional)
        max_wm_samples: upper limit for the number of WM samples (optional)
        num_gm_samples: Number of gray matter samples per voxel (optional)
        """
        runner = CmdInterface('MitkRfTraining')
        runner.add_arg(key='-i', arg=i, check_input=True)
        runner.add_arg(key='-t', arg=t, check_input=True)
        runner.add_arg(key='-o', arg=out_folder + 'forest_mitk.rf', check_output=True)
        if masks is not None:
            runner.add_arg(key='--masks', arg=masks)
        if wm_masks is not None:
            runner.add_arg(key='--wm_masks', arg=wm_masks)
        if volume_modification_images is not None:
            runner.add_arg(key='--volume_modification_images', arg=volume_modification_images)
        if additional_feature_images is not None:
            runner.add_arg(key='--additional_feature_images', arg=additional_feature_images)
        if num_trees is not None:
            runner.add_arg(key='--num_trees', arg=num_trees)
        if max_tree_depth is not None:
            runner.add_arg(key='--max_tree_depth', arg=max_tree_depth)
        if sample_fraction is not None:
            runner.add_arg(key='--sample_fraction', arg=sample_fraction)
        if use_sh_features is not None:
            runner.add_arg(key='--use_sh_features', arg=use_sh_features)
        if sampling_distance is not None:
            runner.add_arg(key='--sampling_distance', arg=sampling_distance)
        if max_wm_samples is not None:
            runner.add_arg(key='--max_wm_samples', arg=max_wm_samples)
        if num_gm_samples is not None:
            runner.add_arg(key='--num_gm_samples', arg=num_gm_samples)
        runner.run()
        return out_folder + 'forest_mitk.rf'

    @staticmethod
    def track_streamline(i: str,
                         out_folder: str,
                         algorithm: str,
                         flip_x: bool = False,
                         flip_y: bool = False,
                         flip_z: bool = False,
                         no_data_interpolation: bool = False,
                         no_mask_interpolation: bool = False,
                         compress: float = None,
                         seeds: int = 1,
                         seed_image: str = None,
                         trials_per_seed: int = 10,
                         max_tracts: int = -1,
                         tracking_mask: str = None,
                         stop_image: str = None,
                         exclusion_image: str = None,
                         ep_constraint: str = None,
                         target_image: str = None,
                         sharpen_odfs: bool = False,
                         cutoff: float = 0.1,
                         odf_cutoff: float = 0,
                         step_size: float = 0.5,
                         min_tract_length: float = 20,
                         angular_threshold: float = None,
                         loop_check: float = None,
                         prior_image: str = None,
                         prior_weight: float = 0.5,
                         restrict_to_prior: bool = False,
                         new_directions_from_prior: bool = False,
                         num_samples: int = 0,
                         sampling_distance: float = 0.25,
                         use_stop_votes: bool = False,
                         use_only_forward_samples: bool = False,
                         tend_f: float = 1,
                         tend_g: float = 0,
                         forest: str = None,
                         use_sh_features: bool = False,
                         additional_images: str = None):
        """
        Perform MITK streamline tractography.

        i: input image (multiple possible for 'DetTensor' algorithm)
        out_folder: output folder
        algorithm: which algorithm to use (Peaks
        flip_x: multiply x-coordinate of direction proposal by -1 (optional)
        flip_y: multiply y-coordinate of direction proposal by -1 (optional)
        flip_z: multiply z-coordinate of direction proposal by -1 (optional)
        no_data_interpolation: don't interpolate input image values (optional)
        no_mask_interpolation: don't interpolate mask image values (optional)
        compress: compress output fibers using the given error threshold (in mm) (optional)
        seeds: number of seed points per voxel (optional)
        seed_image: mask image defining seed voxels (optional)
        trials_per_seed: try each seed N times until a valid streamline is obtained (only for probabilistic tractography) (optional)
        max_tracts: tractography is stopped if the reconstructed number of tracts is exceeded (optional)
        tracking_mask: streamlines leaving the mask will stop immediately (optional)
        stop_image: streamlines entering the mask will stop immediately (optional)
        exclusion_image: streamlines entering the mask will be discarded (optional)
        ep_constraint: determines which fibers are accepted based on their endpoint location - options are NONE
        target_image: effact depends on the chosen endpoint constraint (option ep_constraint) (optional)
        sharpen_odfs: if you are using dODF images as input
        cutoff: set the FA
        odf_cutoff: threshold on the ODF magnitude. this is useful in case of CSD fODF tractography. (optional)
        step_size: step size (in voxels) (optional)
        min_tract_length: minimum fiber length (in mm) (optional)
        angular_threshold: angular threshold between two successive steps
        loop_check: threshold on angular stdev over the last 4 voxel lengths (optional)
        prior_image: tractography prior in thr for of a peak image (optional)
        prior_weight: weighting factor between prior and data. (optional)
        restrict_to_prior: restrict tractography to regions where the prior is valid. (optional)
        new_directions_from_prior: the prior can create directions where there are none in the data. (optional)
        num_samples: number of neighborhood samples that are use to determine the next progression direction (optional)
        sampling_distance: distance of neighborhood sampling points (in voxels) (optional)
        use_stop_votes: use stop votes (optional)
        use_only_forward_samples: use only forward samples (optional)
        tend_f: weighting factor between first eigenvector (f=1 equals FACT tracking) and input vector dependent direction (f=0). (optional)
        tend_g: weighting factor between input vector (g=0) and tensor deflection (g=1 equals TEND tracking) (optional)
        forest: input random forest (HDF5 file) (optional)
        use_sh_features: use SH features (optional)
        additional_images: specify a list of float images that hold additional information (FA
        """
        os.makedirs(out_folder, exist_ok=True)

        tracts = out_folder + os.path.basename(i).split('.')[0] + '_' + algorithm + '_mitk.trk'

        runner = CmdInterface('MitkStreamlineTractography')
        runner.add_arg(key='-i', arg=i, check_input=True)
        runner.add_arg(key='-o', arg=tracts, check_output=True)
        runner.add_arg(key='--algorithm', arg=algorithm)
        if flip_x:
            runner.add_arg(key='--flip_x')
        if flip_y:
            runner.add_arg(key='--flip_y')
        if flip_z:
            runner.add_arg(key='--flip_z')
        if no_data_interpolation:
            runner.add_arg(key='--no_data_interpolation')
        if no_mask_interpolation:
            runner.add_arg(key='--no_mask_interpolation')
        if compress is not None:
            runner.add_arg(key='--compress', arg=compress)
        if seeds is not None:
            runner.add_arg(key='--seeds', arg=seeds)
        if seed_image is not None:
            runner.add_arg(key='--seed_image', arg=seed_image)
        if trials_per_seed is not None:
            runner.add_arg(key='--trials_per_seed', arg=trials_per_seed)
        if max_tracts is not None:
            runner.add_arg(key='--max_tracts', arg=max_tracts)
        if tracking_mask is not None:
            runner.add_arg(key='--tracking_mask', arg=tracking_mask)
        if stop_image is not None:
            runner.add_arg(key='--stop_image', arg=stop_image)
        if exclusion_image is not None:
            runner.add_arg(key='--exclusion_image', arg=exclusion_image)
        if ep_constraint is not None:
            runner.add_arg(key='--ep_constraint', arg=ep_constraint)
        if target_image is not None:
            runner.add_arg(key='--target_image', arg=target_image)
        if sharpen_odfs:
            runner.add_arg(key='--sharpen_odfs')
        if cutoff is not None:
            runner.add_arg(key='--cutoff', arg=cutoff)
        if odf_cutoff is not None:
            runner.add_arg(key='--odf_cutoff', arg=odf_cutoff)
        if step_size is not None:
            runner.add_arg(key='--step_size', arg=step_size)
        if min_tract_length is not None:
            runner.add_arg(key='--min_tract_length', arg=min_tract_length)
        if angular_threshold is not None:
            runner.add_arg(key='--angular_threshold', arg=angular_threshold)
        if loop_check is not None:
            runner.add_arg(key='--loop_check', arg=loop_check)
        if prior_image is not None:
            runner.add_arg(key='--prior_image', arg=prior_image)
        if prior_weight is not None:
            runner.add_arg(key='--prior_weight', arg=prior_weight)
        if restrict_to_prior:
            runner.add_arg(key='--restrict_to_prior')
        if new_directions_from_prior:
            runner.add_arg(key='--new_directions_from_prior')
        if num_samples is not None:
            runner.add_arg(key='--num_samples', arg=num_samples)
        if sampling_distance is not None:
            runner.add_arg(key='--sampling_distance', arg=sampling_distance)
        if use_stop_votes:
            runner.add_arg(key='--use_stop_votes')
        if use_only_forward_samples:
            runner.add_arg(key='--use_only_forward_samples')
        if tend_f is not None:
            runner.add_arg(key='--tend_f', arg=tend_f)
        if tend_g is not None:
            runner.add_arg(key='--tend_g', arg=tend_g)
        if forest is not None:
            runner.add_arg(key='--forest', arg=forest)
        if use_sh_features:
            runner.add_arg(key='--use_sh_features')
        if additional_images is not None:
            runner.add_arg(key='--additional_images', arg=additional_images)
        runner.run()

        return tracts

    @staticmethod
    def mitkglobaltractography(i: str,
                               out_folder: str,
                               parameters: str,
                               mask: str = None):
        """
        Perform MITK global tractography. Save a paramter file for usage using the MITK Diffusion GUI application.
        http://mitk.org/wiki/MitkDiffusion

        i: input image (tensor
        out_folder: output folder
        parameters: parameter file (.gtp)
        mask: binary mask image (optional)
        """
        os.makedirs(out_folder, exist_ok=True)

        tracts = out_folder + os.path.basename(i).split('.')[0] + '_Global_mitk.trk'

        runner = CmdInterface('MitkGlobalTractography')
        runner.add_arg(key='-i', arg=i, check_input=True)
        runner.add_arg(key='-o', arg=tracts, check_output=True)
        runner.add_arg(key='--parameters', arg=parameters)
        if mask is not None:
            runner.add_arg(key='--mask', arg=mask, check_input=True)
        runner.run()

        return tracts


class MRtrixTrackingHelper:

    @staticmethod
    def recon_csd(input_dwi: str, do_flip_bvecs: bool, out_folder: str, algo: str = 'tournier'):
        """ Perform constrained spherical deconvolution modelling and output the resulting spherical harmonics fODFs.
        """
        os.makedirs(out_folder, exist_ok=True)

        if do_flip_bvecs:
            flipper = CmdInterface(flip_bvecs)
            flipper.add_arg('input_dwi', input_dwi, check_input=True)
            input_dwi = input_dwi.replace(os.path.dirname(input_dwi), out_folder)
            input_dwi = input_dwi.replace('.nii.gz', '_flipped.nii.gz')
            flipper.add_arg('output_dwi', input_dwi, check_output=True)
            flipper.run()

        csd_algo = 'csd'
        num_responses = 1
        if algo != 'tournier':
            num_responses = 3
            csd_algo = 'msmt_csd'

        dwi2response = CmdInterface('dwi2response')
        dwi2response.add_arg(arg=algo)
        dwi2response.add_arg(arg=input_dwi, check_input=True)
        for i in range(num_responses):
            dwi2response.add_arg(arg=out_folder + 'response_' + algo + '_' + str(i) + '_mrtrix.txt', check_output=True)
        dwi2response.add_arg(key='-force')
        dwi2response.add_arg('-nthreads', 12)
        dwi2response.add_arg(key='-fslgrad',
                             arg=[input_dwi.replace('.nii.gz', '.bvecs'), input_dwi.replace('.nii.gz', '.bvals')],
                             check_input=True)
        dwi2response.run()

        dwi2fod = CmdInterface('dwi2fod')
        dwi2fod.add_arg(arg=csd_algo)
        dwi2fod.add_arg(arg=input_dwi, check_input=True)
        for i in range(num_responses):
            dwi2fod.add_arg(arg=out_folder + 'response_' + algo + '_' + str(i) + '_mrtrix.txt', check_input=True)
            dwi2fod.add_arg(arg=out_folder + 'odf_' + csd_algo + '_' + str(i) + '_mrtrix.nii.gz', check_output=True)
        dwi2fod.add_arg(key='-force')
        dwi2fod.add_arg('-nthreads', 12)
        dwi2fod.add_arg(key='-fslgrad',
                        arg=[input_dwi.replace('.nii.gz', '.bvecs'), input_dwi.replace('.nii.gz', '.bvals')],
                        check_input=True)
        dwi2fod.run(version_arg='--version')

        return out_folder + 'odf_' + csd_algo + '_' + str(0) + '_mrtrix.nii.gz'

        sh2peaks = CmdInterface('sh2peaks')
        sh2peaks.add_arg(arg=out_folder + 'odf_' + csd_algo + '_0_mrtrix.nii.gz', check_input=True)
        sh2peaks.add_arg(arg=out_folder + 'peaks_' + csd_algo + '_0_mrtrix.nii.gz', check_output=True)
        sh2peaks.add_arg('-threshold', 0.1)
        sh2peaks.run(version_arg='--version')

        flipper = CmdInterface('MitkFlipPeaks')
        flipper.add_arg('-i', out_folder + 'peaks_' + csd_algo + '_0_mrtrix.nii.gz', check_input=True)
        flipper.add_arg('-o', out_folder + 'peaks_' + csd_algo + '_0_flipped_mrtrix.nii.gz', check_output=True)
        flipper.add_arg('-z')
        flipper.run()

    @staticmethod
    def track_streamline(input_image: str,
                         out_folder: str,
                         algo: str,
                         num_streamlines: int,
                         cutoff: float = 0.1,
                         minlength: int = 30,
                         maxlength: int = 200,
                         step: float = None,
                         angle: float = None):
        """ Perform MRtrix streamline tractography.
        """
        os.makedirs(out_folder, exist_ok=True)
        tracts = out_folder + os.path.basename(input_image).split('.')[0] + '_' + algo + '_mrtrix'

        tckgen = CmdInterface('tckgen')
        tckgen.add_arg(arg=input_image, check_input=True)
        if algo == 'Tensor_Det' or algo == 'Tensor_Prob':
            print(algo + ' NOT IMPLEMENTED')
            exit()
            tckgen.add_arg(key='-fslgrad',
                           arg=[input_image.replace('.nii.gz', '.bvecs'), input_image.replace('.nii.gz', '.bvals')])
        tckgen.add_arg(arg=tracts + '.tck', check_output=True)
        tckgen.add_arg('-algorithm', algo)
        tckgen.add_arg('-seed_dynamic', input_image)
        tckgen.add_arg('-nthreads', 12)
        tckgen.add_arg('-select', num_streamlines)
        tckgen.add_arg('-minlength', minlength)
        tckgen.add_arg('-maxlength', maxlength)
        tckgen.add_arg('-cutoff', cutoff)
        if step is not None:
            tckgen.add_arg('-step', step)
        if angle is not None:
            tckgen.add_arg('-angle', angle)
        tckgen.add_arg('-force')
        tckgen.run(version_arg='--version')

        postproc = CmdInterface('MitkFiberProcessing')
        postproc.add_arg('-i', tracts + '.tck', check_input=True)
        postproc.add_arg('--compress', 0.1)
        postproc.add_arg('-o', tracts + '.trk', check_output=True)
        postproc.run()

        return tracts + '.trk'
