import ecto

from opendm import log
from opendm import io
from opendm import system
from opendm import context


class ODMOpenSfMCell(ecto.Cell):
    def declare_params(self, params):
        params.declare("use_exif_size", "The application arguments.", False)
        params.declare("feature_process_size", "The application arguments.", 2400)
        params.declare("feature_min_frames", "The application arguments.", 4000)
        params.declare("processes", "The application arguments.", context.num_cores)
        params.declare("matching_gps_neighbors", "The application arguments.", 8)
        params.declare("matching_gps_distance", "The application arguments.", 0)

        # Features
        params.declare("feature_type", "The application arguments.", "HAHOG")

        # params.declare("surf_hessian_threshold", "The application arguments.", 3000)
        # params.declare("surf_n_octaves", "The application arguments.", 4)
        # params.declare("surf_n_octavelayers", "The application arguments.", 2)
        #
        # params.declare("hahog_peak_threshold", "The application arguments.", 0.00001)
        # params.declare("hahog_edge_threshold", "The application arguments.", 10)
        #
        # params.declare("akaze_omax", "The application arguments.", 4)
        # params.declare("akaze_dthreshold", "The application arguments.", 0.001)
        # params.declare("akaze_descriptor", "The application arguments.", "MSURF")
        # params.declare("akaze_descriptor_size", "The application arguments.", 0)
        # params.declare("akaze_descriptor_channels", "The application arguments.", 3)
        #
        # # Matching
        # params.declare("lowes_ratio", "The application arguments.", 0.8)
        # params.declare("preemptive_lowes_ratio", "The application arguments.", 0.6)
        params.declare("matcher_type", "The application arguments.", "FLANN")
        #
        # # Params for FLANN matching
        # params.declare("flann_branching", "The application arguments.", 16)
        # params.declare("flann_iterations", "The application arguments.", 10)
        # params.declare("flann_checks", "The application arguments.", 200)

    def declare_io(self, params, inputs, outputs):
        inputs.declare("tree", "Struct with paths", [])
        inputs.declare("args", "The application arguments.", {})
        inputs.declare("photos", "list of ODMPhoto's", [])
        outputs.declare("reconstruction", "list of ODMReconstructions", [])

    def process(self, inputs, outputs):

        # Benchmarking
        start_time = system.now_raw()

        log.ODM_INFO('Running ODM OpenSfM Cell')

        # get inputs
        tree = self.inputs.tree
        args = self.inputs.args
        photos = self.inputs.photos

        if not photos:
            log.ODM_ERROR('Not enough photos in photos array to start OpenSfM')
            return ecto.QUIT

        # create working directories     
        system.mkdir_p(tree.opensfm)
        system.mkdir_p(tree.pmvs)

        # check if we rerun cell or not
        rerun_cell = (args.rerun is not None and
                      args.rerun == 'opensfm') or \
                     (args.rerun_all) or \
                     (args.rerun_from is not None and
                      'opensfm' in args.rerun_from)

        if not args.use_pmvs:
            output_file = tree.opensfm_model
        else:
            output_file = tree.opensfm_reconstruction

        # check if reconstruction was done before
        if not io.file_exists(output_file) or rerun_cell:
            # create file list
            list_path = io.join_paths(tree.opensfm, 'image_list.txt')
            with open(list_path, 'w') as fout:
                for photo in photos:
                    fout.write('%s\n' % photo.path_file)

            # create config file for OpenSfM
            config = [
                "use_exif_size: %s" % ('no' if not self.params.use_exif_size else 'yes'),
                "feature_process_size: %s" % self.params.feature_process_size,
                "feature_min_frames: %s" % self.params.feature_min_frames,
                "processes: %s" % self.params.processes,
                "matching_gps_neighbors: %s" % self.params.matching_gps_neighbors,

                # Features
                "feature_type: %s" % self.params.feature_type,

                # "surf_hessian_threshold: %s" % self.params.surf_hessian_threshold,
                # "surf_n_octaves: %s" % self.params.surf_n_octaves,
                # "surf_n_octavelayers: %s" % self.params.surf_n_octavelayers,
                #
                # "hahog_peak_threshold: %s" % self.params.hahog_peak_threshold,
                # "hahog_edge_threshold: %s" % self.params.hahog_edge_threshold,
                #
                # "akaze_omax: %s" % self.params.akaze_omax,
                # "akaze_dthreshold: %s" % self.params.akaze_dthreshold,
                # "akaze_descriptor: %s" % self.params.akaze_descriptor,
                # "akaze_descriptor_size: %s" % self.params.akaze_descriptor_size,
                # "akaze_descriptor_channels: %s" % self.params.akaze_descriptor_channels,
                #
                # # Matching
                # "lowes_ratio: %s" % self.params.lowes_ratio,
                # "preemptive_lowes_ratio: %s" % self.params.preemptive_lowes_ratio,
                "matcher_type: %s" % self.params.matcher_type,
                #
                # "flann_branching: %s" % self.params.flann_branching,
                # "flann_iterations: %s" % self.params.flann_iterations,
                # "flann_checks: %s" % self.params.flann_checks,
            ]

            if args.matcher_distance > 0:
                config.append("matching_gps_distance: %s" % self.params.matching_gps_distance)

            # write config file
            config_filename = io.join_paths(tree.opensfm, 'config.yaml')
            with open(config_filename, 'w') as fout:
                fout.write("\n".join(config))

            # run OpenSfM reconstruction
            matched_done_file = io.join_paths(tree.opensfm, 'matching_done.txt')
            if not io.file_exists(matched_done_file) or rerun_cell:
                system.run('PYTHONPATH=%s %s/bin/opensfm extract_metadata %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
                system.run('PYTHONPATH=%s %s/bin/opensfm detect_features %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
                system.run('PYTHONPATH=%s %s/bin/opensfm match_features %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
                with open(matched_done_file, 'w') as fout:
                    fout.write("Matching done!\n")
            else:
                log.ODM_WARNING('Found a feature matching done progress file in: %s' %
                                matched_done_file)

            if not io.file_exists(tree.opensfm_tracks) or rerun_cell:
                system.run('PYTHONPATH=%s %s/bin/opensfm create_tracks %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
            else:
                log.ODM_WARNING('Found a valid OpenSfM tracks file in: %s' %
                                tree.opensfm_tracks)

            if not io.file_exists(tree.opensfm_reconstruction) or rerun_cell:
                system.run('PYTHONPATH=%s %s/bin/opensfm reconstruct %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
            else:
                log.ODM_WARNING('Found a valid OpenSfM reconstruction file in: %s' %
                                tree.opensfm_reconstruction)

            if not io.file_exists(tree.opensfm_reconstruction_meshed) or rerun_cell:
                system.run('PYTHONPATH=%s %s/bin/opensfm mesh %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
            else:
                log.ODM_WARNING('Found a valid OpenSfM meshed reconstruction file in: %s' %
                                tree.opensfm_reconstruction_meshed)

            if not args.use_pmvs:
                if not io.file_exists(tree.opensfm_reconstruction_nvm) or rerun_cell:
                    system.run('PYTHONPATH=%s %s/bin/opensfm export_visualsfm %s' %
                               (context.pyopencv_path, context.opensfm_path, tree.opensfm))
                else:
                    log.ODM_WARNING('Found a valid OpenSfM NVM reconstruction file in: %s' %
                                    tree.opensfm_reconstruction_nvm)

                system.run('PYTHONPATH=%s %s/bin/opensfm undistort %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
                system.run('PYTHONPATH=%s %s/bin/opensfm compute_depthmaps %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm))
        else:
            log.ODM_WARNING('Found a valid OpenSfM reconstruction file in: %s' %
                            tree.opensfm_reconstruction)

        # check if reconstruction was exported to bundler before
        if not io.file_exists(tree.opensfm_bundle_list) or rerun_cell:
            # convert back to bundler's format
            system.run('PYTHONPATH=%s %s/bin/export_bundler %s' %
                       (context.pyopencv_path, context.opensfm_path, tree.opensfm))
        else:
            log.ODM_WARNING('Found a valid Bundler file in: %s' %
                            tree.opensfm_reconstruction)

        if args.use_pmvs:
            # check if reconstruction was exported to pmvs before
            if not io.file_exists(tree.pmvs_visdat) or rerun_cell:
                # run PMVS converter
                system.run('PYTHONPATH=%s %s/bin/export_pmvs %s --output %s' %
                           (context.pyopencv_path, context.opensfm_path, tree.opensfm, tree.pmvs))
            else:
                log.ODM_WARNING('Found a valid CMVS file in: %s' % tree.pmvs_visdat)

        if args.time:
            system.benchmark(start_time, tree.benchmarking, 'OpenSfM')

        log.ODM_INFO('Running ODM OpenSfM Cell - %s' % system.now())
        return ecto.OK if args.end_with != 'opensfm' else ecto.QUIT
