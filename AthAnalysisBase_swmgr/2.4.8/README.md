example to run inside container:

    docker run -it lukasheinrich/atlas-athanalysisbase-2.4.8 bash
    bash-4.1# mkdir /analysis
    bash-4.1# cd /analysis
    bash-4.1# asetup AthAnalysisBase,2.4.8,here
    bash-4.1# export ROOTCORE_TEST_FILE='root://eosuser.cern.ch//eos/user/l/lheinric/AOD.05352803._000242.pool.root.1'
    bash-4.1# cmt new_skeleton MyPackage
    bash-4.1# cmt find_packages
    bash-4.1# cmt compile
    bash-4.1# kinit lheinric
    bash-4.1# athena MyPackage/MyPackageAlgJobOptions.py
