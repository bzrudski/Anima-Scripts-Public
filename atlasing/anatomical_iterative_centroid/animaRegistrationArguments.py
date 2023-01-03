from dataclasses import dataclass
from enum import IntEnum


class AggregatorTypeNonRigid(IntEnum):
    BALOO = 0
    M_SMOOTHER = 1


class AggregatorTypeRigid(IntEnum):
    M_ESTIMATION = 0
    LEAST_SQUARES = 1
    LEAST_TRIMMED_SQUARES = 2


class SymmetryType(IntEnum):
    ASYMMETRIC = 0
    SYMMETRIC = 1
    KISSING = 2


class OptimizerType(IntEnum):
    EXHAUSTIVE = 0
    BOBYQA = 1


class CartesianAxis(IntEnum):
    X = 0
    Y = 1
    Z = 2


class TransformationType(IntEnum):
    TRANSLATION = 0
    RIGID = 1
    AFFINE = 2
    DIRECTIONAL_AFFINE = 3


class SimilarityMetric(IntEnum):
    MEAN_SQUARES = 0
    CORRELATION_COEFFICIENT = 1
    SQUARED_CORRELATION_COEFFICIENT = 2


class InitialisationType(IntEnum):
    IDENTITY = 0
    ALIGN_GRAVITY_CENTRES = 1
    GRAVITY_PCA_CLOSEST_TRANSFORM = 2


@dataclass
class AnimaDenseSVFBMRegistrationArguments:
    """
    Arguments for dense stationary vector field block matching registration.

    Arguments and default values taken from the help page for `animaDenseSVFBMRegistrationArguments`.
    The arguments have the same meanings and the values have the same interpretations as in the docs.
    """
    last_pyramid_level: int = 0
    number_of_pyramid_levels: int = 3
    exponentiation_order: float = 0
    bch_order: int = 1
    m_estimation_threshold: float = 0.01
    outlier_rejection_sigma: float = 3.0
    elastic_regularisation_sigma: float = 3.0
    extrapolation_sigma: float = 3.0
    aggregator_type: AggregatorTypeNonRigid = AggregatorTypeNonRigid.BALOO
    kissing_point_location: float = 0.5
    symmetry_type: SymmetryType = SymmetryType.ASYMMETRIC
    bobyqa_scale_upper_bound: float = 3.0
    bobyqa_angle_upper_bound: float = 180.0
    bobyqa_translate_upper_bound: int = 3
    exhaustive_search_step: int = 1
    maximum_local_optimizer_iterations: int = 100
    minimum_distance_between_transforms: float = 0.01
    maximum_block_match_iterations: int = 10
    optimizer: OptimizerType = OptimizerType.BOBYQA
    similarity_metric: SimilarityMetric = SimilarityMetric.SQUARED_CORRELATION_COEFFICIENT
    direction_of_directional_affine: CartesianAxis = CartesianAxis.Y
    transformation_type_between_blocks: TransformationType = TransformationType.TRANSLATION
    percentage_of_blocks_kept: float = 0.8
    block_minimum_standard_deviation: float = 5
    block_spacing: int = 2
    block_size: int = 5

    def get_command_args(self) -> list[str]:
        """
        Generate the command line arguments for the stored parameters.

        :return: a list containing the flags and values for the registration.
        """

        return [
            '-l', f"{self.last_pyramid_level}",
            '-p', f"{self.number_of_pyramid_levels}",
            '-e', f"{self.exponentiation_order}",
            '-b', f"{self.bch_order}",
            '--met', f"{self.m_estimation_threshold}",
            '--os', f"{self.outlier_rejection_sigma}",
            '--es', f"{self.elastic_regularisation_sigma}",
            '--fs', f"{self.extrapolation_sigma}",
            '-a', f"{self.aggregator_type.value}",
            '-K', f"{self.kissing_point_location}",
            '-sym-reg', f"{self.symmetry_type.value}",
            '--scu', f"{self.bobyqa_scale_upper_bound}",
            '--aub', f"{self.bobyqa_angle_upper_bound}",
            '--tub', f"{self.bobyqa_translate_upper_bound}",
            '--st', f"{self.exhaustive_search_step}",
            '--oi', f"{self.maximum_local_optimizer_iterations}",
            '--me', f"{self.minimum_distance_between_transforms}",
            '--mi', f"{self.maximum_block_match_iterations}",
            '--opt', f"{self.optimizer.value}",
            '--metric', f"{self.similarity_metric.value}",
            '-d', f"{self.direction_of_directional_affine.value}",
            '-t', f"{self.transformation_type_between_blocks.value}",
            '-k', f"{self.percentage_of_blocks_kept}",
            '-s', f"{self.block_minimum_standard_deviation}",
            '--sp', f"{self.block_spacing}",
            '--bs', f"{self.block_size}",
        ]


@dataclass
class AnimaPyramidalBMRegistrationArguments:
    """
       Arguments for rigid block matching registration.

       Arguments and default values taken from the help page for `animaPyramidalBMRegistration`.
       The arguments have the same meanings and the values have the same interpretations as in the docs.

       The value for the aggregator threshold value was obtained from the source code at
       https://anima.irisa.fr/doxygen/animaPyramidalBMRegistration_8cxx_source.html, as no value was provided
       in the documentation.
       """
    last_pyramid_level: int = 0
    number_of_pyramid_levels: int = 3
    lts_stopping_threshold: float = 0.01
    aggregator_threshold_value: float = 0.5
    aggregator_type: AggregatorTypeRigid = AggregatorTypeRigid.M_ESTIMATION
    kissing_point_location: float = 0.5
    symmetry_type: SymmetryType = SymmetryType.ASYMMETRIC
    bobyqa_scale_upper_bound: float = 3.0
    bobyqa_angle_upper_bound: float = 180.0
    bobyqa_translate_upper_bound: int = 3
    exhaustive_search_step: int = 2
    initialisation_type: InitialisationType = InitialisationType.ALIGN_GRAVITY_CENTRES
    maximum_local_optimizer_iterations: int = 100
    minimum_distance_between_transforms: float = 0.01
    maximum_block_match_iterations: int = 10
    optimizer: OptimizerType = OptimizerType.BOBYQA
    similarity_metric: SimilarityMetric = SimilarityMetric.SQUARED_CORRELATION_COEFFICIENT
    direction_of_directional_affine: CartesianAxis = CartesianAxis.Y
    transformation_type_between_blocks: TransformationType = TransformationType.TRANSLATION
    percentage_of_blocks_kept: float = 0.8
    block_minimum_standard_deviation: float = 5
    block_spacing: int = 5
    block_size: int = 5

    def get_command_args(self) -> list[str]:
        """
        Generate the command line arguments for the stored parameters.

        :return: a list containing the flags and values for the registration.
        """

        return [
            '-l', f"{self.last_pyramid_level}",
            '-p', f"{self.number_of_pyramid_levels}",
            '--lst', f"{self.lts_stopping_threshold}",
            '--at', f"{self.aggregator_threshold_value}",
            '-a', f"{self.aggregator_type.value}",
            '-K', f"{self.kissing_point_location}",
            '-sym-reg', f"{self.symmetry_type.value}",
            '--scu', f"{self.bobyqa_scale_upper_bound}",
            '--aub', f"{self.bobyqa_angle_upper_bound}",
            '--tub', f"{self.bobyqa_translate_upper_bound}",
            '--st', f"{self.exhaustive_search_step}",
            '-I', f"{self.initialisation_type.value}",
            '--oi', f"{self.maximum_local_optimizer_iterations}",
            '--me', f"{self.minimum_distance_between_transforms}",
            '--mi', f"{self.maximum_block_match_iterations}",
            '--opt', f"{self.optimizer.value}",
            '--metric', f"{self.similarity_metric.value}",
            '-d', f"{self.direction_of_directional_affine.value}",
            '-t', f"{self.transformation_type_between_blocks.value}",
            '-k', f"{self.percentage_of_blocks_kept}",
            '-s', f"{self.block_minimum_standard_deviation}",
            '--sp', f"{self.block_spacing}",
            '--bs', f"{self.block_size}",
        ]
