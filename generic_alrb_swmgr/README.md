#Example Usage

build a certain release by setting the buildargs

    docker build \
    --build-arg BUILDARG_GCCVERSION=4.9.3 \
    --build-arg ASG_ATHENA_RELEASEVERSION=2.4.8 \
    --build-arg ASG_ATHENA_RELEASENAME=AthAnalysisBase \
    --build-arg ASG_ATHENA_RELEASEARCH=x86_64-slc6-gcc49-opt \
    -t lukasheinrich/alrb_athanalysisbase_2_4_8 .


