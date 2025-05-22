# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import copy
import os
from dataclasses import asdict

import numpy as np
import wandb

from benchmarks.configs.defaults import (
    default_all_noisy_sensor_module,
    default_evidence_1lm_config,
    min_eval_steps,
)
from benchmarks.configs.monty_world_habitat_experiments import (
    randrot_noise_sim_on_scan_monty_world,
)
from benchmarks.configs.names import MyExperiments
from benchmarks.configs.pretraining_experiments import only_surf_agent_training_10obj
from benchmarks.configs.ycb_experiments import (
    default_all_noisy_surf_agent_sensor_module,
)
from tbp.monty.frameworks.config_utils.config_args import (
    MontyArgs,
    MotorSystemConfigCurInformedSurfaceGoalStateDriven,
    MotorSystemConfigInformedNoTransStepS20,
    PatchAndViewMontyConfig,
    PretrainLoggingConfig,
    SurfaceAndViewSOTAMontyConfig,
    get_cube_face_and_corner_views_rotations,
)
from tbp.monty.frameworks.config_utils.make_dataset_configs import (
    EnvironmentDataloaderPerObjectArgs,
    EvalExperimentArgs,
    PredefinedObjectInitializer,
    RandomRotationObjectInitializer,
    get_object_names_by_idx,
)
from tbp.monty.frameworks.environment_utils.transforms import (
    DepthTo3DLocations,
)
from tbp.monty.frameworks.environments.embodied_data import EnvironmentDataset
from tbp.monty.frameworks.environments.everything_is_awesome import (
    EverythingIsAwesomeActionSampler,
    EverythingIsAwesomeDataLoader,
    EverythingIsAwesomeEnvironment,
)
from tbp.monty.frameworks.experiments.everything_is_awesome import (
    EverythingIsAwesomeExperiment,
)
from tbp.monty.frameworks.loggers.monty_handlers import (
    BasicCSVStatsHandler,
    DetailedJSONHandler,
    ReproduceEpisodeHandler,
)
from tbp.monty.frameworks.models.evidence_matching import (
    EvidenceGraphLM,
    MontyForEvidenceGraphMatching,
)
from tbp.monty.frameworks.models.goal_state_generation import EvidenceGoalStateGenerator
from tbp.monty.frameworks.models.motor_policies import BasePolicy
from tbp.monty.frameworks.models.motor_system import MotorSystem
from tbp.monty.frameworks.models.sensor_modules import (
    DetailedLoggingSM,
    FeatureChangeSM,
)
from tbp.monty.simulators.habitat.configs import (
    PatchViewFinderMontyWorldMountHabitatDatasetArgs,
    SurfaceViewFinderMontyWorldMountHabitatDatasetArgs,
)

# A set of objects that can be obtained internationally and used to test Monty's
# performance on those physical objects.
TBP_ROBOT_LAB_OBJECTS = [
    "numenta_mug",
    "montys_brain",
    "montys_heart",
    "ramen_pack",
    "hot_sauce",
    "harissa_oil",
    "tomato_soup_can",
    "mustard_bottle",
    "tuna_fish_can",
    "potted_meat_can",
]


# ============== TRAINING CONFIGS ===============

monty_models_dir = os.path.expanduser(os.getenv("MONTY_MODELS"))
pretrained_dir = os.path.expanduser(
    os.path.join(monty_models_dir, "pretrained_robot_v1")
)

train_rotations_all = get_cube_face_and_corner_views_rotations()


tbp_robot_lab_dataset_args = SurfaceViewFinderMontyWorldMountHabitatDatasetArgs()


tbp_robot_lab_dataset_args.env_init_args["data_path"] = os.path.join(
    os.environ["MONTY_DATA"], "tbp_robot_lab"
)


only_surf_agent_training_tbp_robot_lab = copy.deepcopy(only_surf_agent_training_10obj)


only_surf_agent_training_tbp_robot_lab.update(
    logging_config=PretrainLoggingConfig(
        output_dir=pretrained_dir,
        run_name="surf_agent_1lm_tbp_robot_lab",
    ),
    dataset_args=tbp_robot_lab_dataset_args,
    train_dataloader_args=EnvironmentDataloaderPerObjectArgs(
        object_names=get_object_names_by_idx(0, 10, object_list=TBP_ROBOT_LAB_OBJECTS),
        object_init_sampler=PredefinedObjectInitializer(rotations=train_rotations_all),
    ),
)


# ============== INFERENCE CONFIGS ==============

model_path_tbp_robot_lab = os.path.join(
    pretrained_dir,
    "surf_agent_1lm_tbp_robot_lab/pretrained/",
)


tbp_robot_lab_dist_dataset_args = PatchViewFinderMontyWorldMountHabitatDatasetArgs()


tbp_robot_lab_dist_dataset_args.env_init_args["data_path"] = os.path.join(
    os.environ["MONTY_DATA"], "tbp_robot_lab"
)


randrot_noise_dist_sim_on_scan_tbp_robot_lab = copy.deepcopy(
    randrot_noise_sim_on_scan_monty_world
)


randrot_noise_dist_sim_on_scan_tbp_robot_lab.update(
    experiment_args=EvalExperimentArgs(
        model_name_or_path=model_path_tbp_robot_lab,
        n_eval_epochs=10,
    ),
    monty_config=PatchAndViewMontyConfig(
        sensor_module_configs=dict(
            sensor_module_0=default_all_noisy_sensor_module,
            sensor_module_1=dict(
                sensor_module_class=DetailedLoggingSM,
                sensor_module_args=dict(
                    sensor_module_id="view_finder",
                    save_raw_obs=False,
                ),
            ),
        ),
        learning_module_configs=default_evidence_1lm_config,
        monty_args=MontyArgs(min_eval_steps=min_eval_steps),
        # Not using the hypothesis-driven motor system here to compare to a fixed sensor
        # setup.
        motor_system_config=MotorSystemConfigInformedNoTransStepS20(),
    ),
    dataset_args=tbp_robot_lab_dist_dataset_args,
    eval_dataloader_args=EnvironmentDataloaderPerObjectArgs(
        object_names=get_object_names_by_idx(0, 10, object_list=TBP_ROBOT_LAB_OBJECTS),
        object_init_sampler=RandomRotationObjectInitializer(),
    ),
)


randrot_noise_surf_sim_on_scan_tbp_robot_lab = copy.deepcopy(
    randrot_noise_dist_sim_on_scan_tbp_robot_lab
)


randrot_noise_surf_sim_on_scan_tbp_robot_lab.update(
    monty_config=SurfaceAndViewSOTAMontyConfig(
        sensor_module_configs=dict(
            sensor_module_0=default_all_noisy_surf_agent_sensor_module,
            sensor_module_1=dict(
                sensor_module_class=DetailedLoggingSM,
                sensor_module_args=dict(
                    sensor_module_id="view_finder",
                    save_raw_obs=False,
                ),
            ),
        ),
        learning_module_configs=default_evidence_1lm_config,
        monty_args=MontyArgs(min_eval_steps=min_eval_steps),
        # In our real-world experiments the sensor is now able to move around the object
        # so we also allow this here for the simlation comparison.
        motor_system_config=MotorSystemConfigCurInformedSurfaceGoalStateDriven(),
    ),
    dataset_args=tbp_robot_lab_dataset_args,
)


ACTUATOR_SERVER_URI = "PYRO:motor@192.168.0.235:3514"
AGENT_ID = "agent_id_0"
DEPTH_SERVER_URI = "PYRO:depth@192.168.0.235:3513"
DEPTH_CLIP_VALUE_RR = 1.8  # Based on physical measurements
"""The depth value to clip observations that miss the object."""
PITCH_DIAMETER_RR = 0.12318841  # Based on physical measurements
"""The pitch diameter in units of robot_radius."""
RGB_SERVER_URI = "PYRO:rgb@192.168.0.143:3512"
SENSOR_ID = "patch"
SENSOR_RESOLUTION = [70, 70]

everything_is_awesome_eval = dict(
    experiment_class=EverythingIsAwesomeExperiment,
    experiment_args=dict(
        do_train=False,
        do_eval=True,
        max_eval_steps=500,
        max_train_steps=1000,
        max_total_steps=4 * 500,
        n_eval_epochs=1,
        n_train_epochs=1,
        min_lms_match=1,
        model_name_or_path="",
        seed=1337,
        show_sensor_output=False,  # Use this for online visualization
    ),
    logging_config=dict(
        monty_log_level="DETAILED",
        monty_handlers=[
            BasicCSVStatsHandler,
            DetailedJSONHandler,
            ReproduceEpisodeHandler,
        ],
        wandb_handlers=[],
        python_log_level="INFO",
        python_log_to_file=True,
        python_log_to_stdout=True,
        output_dir=os.path.join(monty_models_dir, "everything_is_awesome"),
        run_name="",
        resume_wandb_run=False,
        wandb_id=wandb.util.generate_id(),
        wandb_group="debugging",
        log_parallel_wandb=False,
    ),
    monty_config=dict(
        monty_class=MontyForEvidenceGraphMatching,
        monty_args=dict(
            num_exploratory_steps=1_000,
            min_eval_steps=3,
            min_train_steps=3,
            max_total_steps=2_500,
        ),
        learning_module_configs=dict(
            learning_module_0=dict(
                learning_module_class=EvidenceGraphLM,
                learning_module_args=dict(
                    max_match_distance=0.01,  # TODO: Will this work for radii units?
                    tolerances=dict(
                        patch=dict(
                            hsv=np.array([0.1, 0.2, 0.2]),
                            principal_curvatures_log=np.ones(2),
                        )
                    ),
                    feature_weights=dict(
                        patch=dict(
                            hsv=np.array([1, 0.5, 0.5]),
                        )
                    ),
                    x_percent_threshold=20,
                    max_nneighbors=10,
                    evidence_update_threshold="80%",
                    max_graph_size=0.3,  # TODO: Will this work for radii units?
                    num_model_voxels_per_dim=100,
                    gsg_class=EvidenceGoalStateGenerator,
                    gsg_args=dict(
                        goal_tolerances=dict(
                            location=0.015,  # TODO: Will this work for radii units?
                        ),
                        elapsed_steps_factor=10,
                        min_post_goal_success_steps=5,
                        x_percent_scale_factor=0.75,
                        desired_object_distance=0.03,  # TODO: Will this work for radii units?  # noqa: E501
                    ),
                ),
            ),
        ),
        sensor_module_configs=dict(
            sensor_module_0=dict(
                sensor_module_class=FeatureChangeSM,
                sensor_module_args=dict(
                    sensor_module_id=SENSOR_ID,
                    features=[
                        # morphological featuers (necessary)
                        "pose_vectors",
                        "pose_fully_defined",
                        "on_object",
                        # non-morphological features (optional)
                        "object_coverage",
                        "min_depth",
                        "mean_depth",
                        "hsv",
                        "principal_curvatures",
                        "principal_curvatures_log",
                    ],
                    delta_thresholds=dict(
                        on_object=0,
                        n_steps=20,
                        hsv=[0.1, 0.1, 0.1],
                        pose_vectors=[np.pi / 4, np.pi * 2, np.pi * 2],
                        principal_curvatures_log=[2, 2],
                        distance=0.01,
                    ),
                    surf_agent_sm=False,
                    save_raw_obs=False,
                ),
            )
        ),
        motor_system_config=dict(
            motor_system_class=MotorSystem,
            motor_system_args=dict(
                policy_class=BasePolicy,
                policy_args=dict(
                    action_sampler_class=EverythingIsAwesomeActionSampler,
                    action_sampler_args={},
                    agent_id=AGENT_ID,
                    switch_frequency=1.0,
                ),
            ),
        ),
        sm_to_agent_dict=dict(
            patch=AGENT_ID,
        ),
        sm_to_lm_matrix=[[0]],
        lm_to_lm_matrix=None,
        lm_to_lm_vote_matrix=None,
    ),
    dataset_class=EnvironmentDataset,
    dataset_args=dict(
        env_init_func=EverythingIsAwesomeEnvironment,
        env_init_args=dict(
            actuator_server_uri=ACTUATOR_SERVER_URI,
            depth_server_uri=DEPTH_SERVER_URI,
            pitch_diameter_rr=PITCH_DIAMETER_RR,
            rgb_server_uri=RGB_SERVER_URI,
        ),
        transform=[
            DepthTo3DLocations(
                agent_id=AGENT_ID,
                clip_value=DEPTH_CLIP_VALUE_RR,
                depth_clip_sensors=[SENSOR_ID],
                get_all_points=True,
                resolutions=[SENSOR_RESOLUTION],
                sensor_ids=[SENSOR_ID],
                use_semantic_sensor=False,
                world_coord=True,
            ),
        ],
        rng=None,
    ),
    eval_dataloader_class=EverythingIsAwesomeDataLoader,
    eval_dataloader_args=dict(
        object_name="tissue_box",
    ),
)


experiments = MyExperiments(
    everything_is_awesome_eval=everything_is_awesome_eval,
    only_surf_agent_training_tbp_robot_lab=only_surf_agent_training_tbp_robot_lab,
    randrot_noise_dist_sim_on_scan_tbp_robot_lab=randrot_noise_dist_sim_on_scan_tbp_robot_lab,
    randrot_noise_surf_sim_on_scan_tbp_robot_lab=randrot_noise_surf_sim_on_scan_tbp_robot_lab,
)
CONFIGS = asdict(experiments)
