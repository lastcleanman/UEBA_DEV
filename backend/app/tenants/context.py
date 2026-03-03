from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    root: Path

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def data_raw_dir(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def data_processed_dir(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def models_dir(self) -> Path:
        return self.root / "models"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def parsers_dir(self) -> Path:
        return self.artifacts_dir / "parsers"

    @property
    def metrics_dir(self) -> Path:
        return self.root / "metrics"