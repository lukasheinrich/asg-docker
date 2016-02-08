#!/bin/bash
mkdir /analysis
cd /analysis
export AtlasSetup=/code/AtlasSetup
source $AtlasSetup/scripts/asetup.sh AthAnalysisSUSY,2.3.41,here
curl -O http://physics.nyu.edu/~lh1132/AOD.05352803._000242.pool.root.1
export PATHRESOLVER_ALLOWHTTPDOWNLOAD=1
ROOTCORE_TEST_FILE=AOD.05352803._000242.pool.root.1 athena.py SUSYTools/applyST.py
