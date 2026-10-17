"""
Módulo de Aprendizaje Continuo (Continual Learning) para CLODA-RAG
==================================================================
Arquitectura de Bucle Cerrado Doctoral para SoeBOT v7.0.
"""

from .dataset_curator import DatasetCurator, DPOTriplet, SFTExample
from .train_worker import TrainConfig, TrainWorker, TrainingResult
from .drift_detector import DriftThresholds, DriftMetrics, TriggerEvent, DriftDetector
from .model_registry import ModelVersion, ModelRegistry
from .doctoral_evaluator import ConditionMetrics, StatisticalComparison, DoctoralEvaluator

__all__ = [
    "DatasetCurator",
    "DPOTriplet",
    "SFTExample",
    "TrainConfig",
    "TrainWorker",
    "TrainingResult",
    "DriftThresholds",
    "DriftMetrics",
    "TriggerEvent",
    "DriftDetector",
    "ModelVersion",
    "ModelRegistry",
    "ConditionMetrics",
    "StatisticalComparison",
    "DoctoralEvaluator",
]
