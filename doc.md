<!-- Template from https://github.com/othneildrew/Best-README-Template -->
<a id="readme-top"></a>


<!-- PROJECT LOGO -->
<div align="center">
  <h2 align="center">LAAS-LAPLACE Hackathon Test Bench</h2>

  <p align="center">
    This project proposes a highly automated power device characterization tool.
    <br />
  </p>
</div>


[![Github][github]][github-url]
![Python][python]



<!-- TABLE OF CONTENTS -->
<summary>Table of Contents</summary>
<ol>
  <li><a href="#getting-started">Getting started</a></li>
  <li><a href="#run-automated-test">Run automated test</a></li>
  <li><a href="#licencing">Licencing</a></li>
</ol>



<!-- GETTING STARTED -->
## Getting started
1. Clone the repository to your local machine:
```bash
git clone https://github.com/your_username/laas-laplace-hackathon.git
```
2. Install the required packages. It is recommended to work in a virtual Python environment (or conda environment) to avoid version conflicts.
```bash
python -m venv dev-env
dev-env/bin/activate
pip install -r requirements.txt
```

<u>Description of files:</u>
| Script name                      |  Description                              |
|----------------------------------|-------------------------------------------|
|  InitZplus_vX.py                 |  Setup tools such as listy instruments    |
|  Opposition_GenerateJson_vX.py   |  Generate JSON files from base config     |
|  Supervisor_vX                   |  Class with all function required         |
|  supervisor_script_vX            |  Runs test from JSON file                 |

Many of the above tools can also be run directly from the InitZplus_vX.py tool by using the following arguments :
- `list` : list connected devices
- `single` : set a single continuous operating point
- `tdk` : test connection to tdk power supply
- `run` : runs full automated test from json files

usage:
```bash
python InitZplus_vX.py <arg>
```


<!-- RUN TEST -->
## Run automated test
1. List all detected instruments to get their address:
```bash
python InitZplus_v2.py list
```
Update the [base-config.json](base-config.json) file with the address for each instrument. Note that this can either be a USB address or a IP address.

2. Generate test configuration files:
```bash
python Opposition_GenerateJson_v1_2.py
```
With the default `base-config.json` this should create the following file structure:
```
your/work/folder
├── PhaseShift
|   ├── Voltage_40 
│   │   └── PhaseShift_Voltage_40V_XXX.json
|   ├── Voltage_60 
│   │   └── PhaseShift_Voltage_60V_XXX.json
|   └── Voltage_80 
│       └── PhaseShift_Voltage_80V_XXX.json
└── DutyShift
    ├── Voltage_40 
    │   └── PhaseShift_Voltage_40V_XXX.json
    ├── Voltage_60 
    │   └── PhaseShift_Voltage_60V_XXX.json
    └── Voltage_80 
        └── PhaseShift_Voltage_80V_XXX.json
```

3. Launch all tests:
```bash
python InitZplus_v2.py run
```
All the generated data will be stored in the associated subfolder of each json config file.



<!-- LICENCE -->
## Licence
[![Licence: GPL v3][gpl3-badge]][gpl3-url]

This work is licensed under a GNU GPL v3 licence. See [LICENCE.md](LICENCE.md) for more information.



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[python]: images/badge/python.svg
[github]: images/badge/github.svg
[github-url]: https://github.com
[gpl3-url]: https://www.gnu.org/licenses/gpl-3.0
[gpl3-badge]: https://img.shields.io/badge/License-GPLv3-blue.svg
