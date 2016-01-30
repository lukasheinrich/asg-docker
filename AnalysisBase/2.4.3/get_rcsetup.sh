rcSetup() {
    export rcSetupSite=/atlas-asg
    export PATHRESOLVER_ALLOWHTTPDOWNLOAD=1
    source /atlas-asg/rcSetup/latest/rcSetup.sh $*
}
