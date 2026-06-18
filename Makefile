# MERRA-2 Data Pipeline for PV, Wind, Biomass, and Geothermal Simulations
#
# Usage (run from the project root):
#   make pv 2019 germany
#   make pv 2019 2020 germany
#   make biomass 2019 germany
#   make geothermal 2019 2022 germany
#   make combine-pv 2019 germany
#   make list-countries
#   make install
#
# Chain multiple years:
#   make pv 2019 germany && make pv 2020 germany

# Prefer the original conda env when present, otherwise fall back to python3.
DEFAULT_PYTHON := $(HOME)/miniconda3/envs/pysamnrel/bin/python
PYTHON ?= $(if $(wildcard $(DEFAULT_PYTHON)),$(DEFAULT_PYTHON),python3)
# The package lives in src/data_pipeline; run `python -m data_pipeline` from src/.
ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PARENT_DIR := $(abspath $(ROOT_DIR)/src)

# Extra options (e.g., OPTS="--verbose")
OPTS ?=

# Capture positional arguments: everything after the target name
TARGETS := pv wind biomass geothermal combine-pv combine-wind combine-biomass combine-geothermal install list-countries help
ARGS := $(filter-out $(TARGETS),$(MAKECMDGOALS))

# Prevent make from treating positional args as targets
%:
	@:

.PHONY: pv wind biomass geothermal combine-pv combine-wind combine-biomass combine-geothermal install list-countries help

pv:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline pv $(ARGS) $(OPTS)

wind:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline wind $(ARGS) $(OPTS)

biomass:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline biomass $(ARGS) $(OPTS)

geothermal:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline geothermal $(ARGS) $(OPTS)

combine-pv:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline pv $(ARGS) --skip-download $(OPTS)

combine-wind:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline wind $(ARGS) --skip-download $(OPTS)

combine-biomass:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline biomass $(ARGS) --skip-download $(OPTS)

combine-geothermal:
	cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline geothermal $(ARGS) --skip-download $(OPTS)

install:
	$(PYTHON) -m pip install -r requirements.txt

list-countries:
	@cd $(PARENT_DIR) && $(PYTHON) -m data_pipeline --list-countries

help:
	@echo "MERRA-2 Data Pipeline"
	@echo ""
	@echo "Usage:"
	@echo "  make pv <year> <country>                       Single year"
	@echo "  make pv <start_year> <end_year> <country>      Year range"
	@echo "  make wind <year> <country>                      Single year"
	@echo "  make biomass <year> <country>                   Single year"
	@echo "  make geothermal <year> <country>                Single year"
	@echo "  make combine-pv <year> <country>                Combine only (skip download)"
	@echo "  make combine-biomass <year> <country>           Combine only (skip download)"
	@echo "  make list-countries                              List supported countries"
	@echo "  make install                                     Install Python dependencies"
	@echo ""
	@echo "Options:"
	@echo "  OPTS=\"--verbose\"              Verbose logging"
	@echo "  OPTS=\"--skip-combine\"         Download only"
	@echo ""
	@echo "Examples:"
	@echo "  make pv 2019 germany"
	@echo "  make pv 2019 2020 germany"
	@echo "  make wind 2019 europe"
	@echo "  make biomass 2019 germany"
	@echo "  make geothermal 2019 2022 germany"
	@echo "  make combine-pv 2019 germany"
	@echo ""
	@echo "Requires EARTHDATA_USERNAME and EARTHDATA_PASSWORD in .env"
