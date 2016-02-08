example to run inside container:

    export AtlasSetup=/code/software/AthAnalysisBase/x86_64-slc6-gcc49-opt/2.3.43/AtlasSetup
    git clone https://github.com/lukasheinrich/quickana-tutorial-ath.git /analysis
    cd /analysis/
    source $AtlasSetup/scripts/asetup.sh AthAnalysisBase,2.3.43,here
    cd MyAnalysis/cmt/
    cmt br cmt config
    cmt br cmt make
    cd ../../
    ./tests/runtest.sh

