from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Tuple, Any, Type, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


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
            '--sym-reg', f"{self.symmetry_type.value}",
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
            '--sym-reg', f"{self.symmetry_type.value}",
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


def _parse_enum(value: str | int, enum_type: Type[IntEnum]) -> IntEnum:
    """
    Parse an IntEnum from a given string or integer.

    The `value` argument contains either the integer that corresponds to the desired enumerated value or it contains
    a string with any of the integer value or the name of the desired enum value. This function is case-insensitive
    and the value may contain spaces or dashes instead of underscores.

    This function throws:

    * `ValueError` if the value supplied is an integer that does not match any of the enumerated values.
    * `KeyError` if the value supplied is a string that does not match any of the enumerated keys.

    :param value: The value to parse from the enumerated type (int or str).
    :param enum_type: The enumerated type from which a value is desired.
    :return: The specific instance of the enumerated type that corresponds to the value supplied.
    """
    if isinstance(value, int):
        return enum_type(value)
    elif isinstance(value, str):
        if value.isdigit():
            return enum_type(int(value))
        else:
            cleaned_value = value.upper().replace(" ", "_").replace("-", "_")
            return enum_type[cleaned_value]


def parse_registration_parameters(
        filename: str,
        default_rigid_parameters: Optional[AnimaPyramidalBMRegistrationArguments] = None,
        default_non_rigid_parameters: Optional[AnimaDenseSVFBMRegistrationArguments] = None,
) -> Tuple[AnimaPyramidalBMRegistrationArguments, AnimaDenseSVFBMRegistrationArguments]:
    """
    Parse the registration parameters.

    This function parses the registration parameters from a TOML file. The file should contain at most two sections:

    * `[AnimaPyramidalBMRegistrationArguments]`
    * `[AnimaDenseSVFBMRegistrationArguments]`

    Within each section, the arguments may be provided as listed in the class attributes above. Any key that is not
    provided will result in the default value being set for the corresponding registration parameter. For the values
    which are specified by enumerated types, acceptable values are either the integer value or the name of the option
    as a string. This string is case-insensitive and any underscores may be replaced by spaces or dashes. None of the
    letters may be changed, though. For example, in the case of the `aggregator_type` in `[
    AnimaPyramidalBMRegistrationArguments]`, the following are all acceptable and equivalent:

    * `2` (this works both when passed as an integer or a string)
    * `"least trimmed squares"`
    * `"LEAST-TRIMMED-SQUARES"`
    * `"leAsT TriMmeD_Squares"`

    The following are acceptable keys:

    * AnimaPyramidalBMRegistrationArguments

        * last_pyramid_level
        * number_of_pyramid_levels
        * lts_stopping_threshold
        * aggregator_threshold_value
        * aggregator_type
        * kissing_point_location
        * symmetry_type
        * bobyqa_scale_upper_bound
        * bobyqa_angle_upper_bound
        * bobyqa_translate_upper_bound
        * exhaustive_search_step
        * initialisation_type
        * maximum_local_optimizer_iterations
        * minimum_distance_between_transforms
        * maximum_block_match_iterations
        * optimizer
        * similarity_metric
        * direction_of_directional_affine
        * transformation_type_between_blocks
        * percentage_of_blocks_kept
        * block_minimum_standard_deviation
        * block_spacing
        * block_size

    * AnimaDenseSVFBMRegistrationArguments:

        * last_pyramid_level
        * number_of_pyramid_levels
        * exponentiation_order
        * bch_order
        * m_estimation_threshold
        * outlier_rejection_sigma
        * elastic_regularisation_sigma
        * extrapolation_sigma
        * aggregator_type
        * kissing_point_location
        * symmetry_type
        * bobyqa_scale_upper_bound
        * bobyqa_angle_upper_bound
        * bobyqa_translate_upper_bound
        * exhaustive_search_step
        * maximum_local_optimizer_iterations
        * minimum_distance_between_transforms
        * maximum_block_match_iterations
        * optimizer
        * similarity_metric
        * direction_of_directional_affine
        * transformation_type_between_blocks
        * percentage_of_blocks_kept
        * block_minimum_standard_deviation
        * block_spacing
        * block_size

    :param filename: the TOML file containing the registration parameters
    :param default_rigid_parameters: Default rigid parameters, passed as an `AnimaPyramidalBMRegistrationArguments`
           object. Any fields present in the TOML file will overwrite fields present in the default. If the TOML file
           does not contain any parameters for the rigid registration, this exact same object is returned.
    :param default_non_rigid_parameters: Default non-rigid parameters, passed as an
           `AnimaDenseSVFBMRegistrationArguments` object. Any fields present in the TOML file will overwrite fields
           present in the default. If the TOML file does not contain any parameters for the non-rigid registration,
           this exact same object is returned.
    :return: a tuple containing the `AnimaPyramidalBMRegistrationArguments` and `AnimaDenseSVFBMRegistrationArguments`
    """

    with open(filename, "rb") as toml_file:
        parsed_parameters: dict[str, dict[str, Any]] = tomllib.load(toml_file)

        # Define our variables for later
        anima_pyramidal_bm_registration_arguments: AnimaPyramidalBMRegistrationArguments
        anima_dense_svf_bm_registration_arguments: AnimaDenseSVFBMRegistrationArguments

        # Determine whether we have a section for the rigid arguments.
        if "AnimaPyramidalBMRegistrationArguments" in parsed_parameters:
            rigid_parameters = parsed_parameters["AnimaPyramidalBMRegistrationArguments"]

            # Deal with the enums.
            rigid_enum_keys = {
                "aggregator_type": AggregatorTypeRigid,
                "symmetry_type": SymmetryType,
                "initialisation_type": InitialisationType,
                "optimizer": OptimizerType,
                "similarity_metric": SimilarityMetric,
                "direction_of_directional_affine": CartesianAxis,
                "transformation_type_between_blocks": TransformationType,
            }

            for rigid_enum_key in rigid_enum_keys:
                if rigid_enum_key in rigid_parameters:
                    raw_value = rigid_parameters[rigid_enum_key]
                    enum_type = rigid_enum_keys[rigid_enum_key]

                    rigid_parameters[rigid_enum_key] = _parse_enum(raw_value, enum_type)

            if default_rigid_parameters is not None:
                anima_pyramidal_bm_registration_arguments = replace(default_rigid_parameters, **rigid_parameters)
            else:
                anima_pyramidal_bm_registration_arguments = AnimaPyramidalBMRegistrationArguments(**rigid_parameters)
        else:
            if default_rigid_parameters is not None:
                anima_pyramidal_bm_registration_arguments = default_rigid_parameters
            else:
                anima_pyramidal_bm_registration_arguments = AnimaPyramidalBMRegistrationArguments()

        if "AnimaDenseSVFBMRegistrationArguments" in parsed_parameters:
            non_rigid_parameters = parsed_parameters["AnimaDenseSVFBMRegistrationArguments"]

            # Deal with the enums.
            non_rigid_enum_keys = {
                "aggregator_type": AggregatorTypeNonRigid,
                "symmetry_type": SymmetryType,
                "optimizer": OptimizerType,
                "similarity_metric": SimilarityMetric,
                "direction_of_directional_affine": CartesianAxis,
                "transformation_type_between_blocks": TransformationType,
            }

            for non_rigid_enum_key in non_rigid_enum_keys:
                if non_rigid_enum_key in non_rigid_parameters:
                    raw_value = non_rigid_parameters[non_rigid_enum_key]
                    enum_type = non_rigid_enum_keys[non_rigid_enum_key]

                    non_rigid_parameters[non_rigid_enum_key] = _parse_enum(raw_value, enum_type)

            if default_non_rigid_parameters is not None:
                anima_dense_svf_bm_registration_arguments = replace(default_non_rigid_parameters,
                                                                    **non_rigid_parameters)
            else:
                anima_dense_svf_bm_registration_arguments = AnimaDenseSVFBMRegistrationArguments(**non_rigid_parameters)
        else:
            if default_non_rigid_parameters is not None:
                anima_dense_svf_bm_registration_arguments = default_non_rigid_parameters
            else:
                anima_dense_svf_bm_registration_arguments = AnimaDenseSVFBMRegistrationArguments()

        toml_file.close()

        return anima_pyramidal_bm_registration_arguments, anima_dense_svf_bm_registration_arguments
