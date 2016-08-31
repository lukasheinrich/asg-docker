FROM cern/slc6-base
RUN useradd atlas
RUN curl -o /etc/yum.repos.d/egi-trustanchors.repo http://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.repo

RUN yum install -y svn
RUN yum install -y nano
RUN yum groupinstall -y "Development Tools"
RUN yum install -y git tar libmpc-devel mpfr-devel gmp-devel tar bzip2 git make  wget
RUN yum install -y \
       	cmake which zlib zlib-devel krb5-devel krb5-libs krb5-appl-clients \
        binutils libX11-devel libXpm-devel libXft-devel libXext-devel \
        openssl-devel pcre-devel mesa-libGL-devel mesa-libGLU-devel glew-devel \
        ftgl-devel mysql-devel fftw-devel cfitsio-devel graphviz-devel avahi-compat-libdns_sd-devel \
        libldap-dev python-devel libxml2-devel gsl-static
RUN yum --nogpgcheck -y install ca-policy-egi-core



ENV ATLAS_SW_BASE=/atlas_software
ENV ALRB_localConfigDir=$HOME/myLocalConfig
ENV ALRB_RELOCATECVMFS="YES"
ENV ATLAS_LOCAL_ROOT_BASE=$ATLAS_SW_BASE/atlas.cern.ch/repo/ATLASLocalRootBase


#make pseudo cvmfs
RUN mkdir -p $ATLAS_SW_BASE/atlas.cern.ch/repo
RUN mkdir -p $ATLAS_SW_BASE/atlas.cern.ch/repo/sw
RUN chown -R atlas $ATLAS_SW_BASE

#####################################
USER atlas
WORKDIR /home/atlas
RUN svn co http://svn.cern.ch/guest/atcansupport/manageTier3SW/trunk userSupport/manageTier3SW
WORKDIR /home/atlas/userSupport/manageTier3SW

#all pack
#pacman,AtlasSetup,sw-mgr,boost,dq2,cmt,ganga,gcc,pandaClient,pyAmi,python,xrootd,root,rucio,rucio-clients,emi,agis,rcsetup,faxtools,atlantis,davix,cmake,PoD,xml,eiclient,gsl,fftw,git

RUN  ./updateManageTier3SW.sh --installALRB="$ATLAS_SW_BASE/atlas.cern.ch/repo" --installOnly="pacman,sw-mgr"
RUN  ./updateManageTier3SW.sh --installOnly='emi'
RUN  ./updateManageTier3SW.sh --installOnly='git'
RUN  ./updateManageTier3SW.sh --installOnly='AtlasSetup'
RUN  ./updateManageTier3SW.sh --installOnly='rcsetup'




#####################################
USER root

RUN echo "alias setupATLAS='source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh'" >> ~/.bashrc
RUN cp -r /etc/grid-security/certificates $ATLAS_LOCAL_ROOT_BASE/etc/grid-security-emi

#####################################
USER atlas
RUN echo "alias setupATLAS='source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh'" >> ~/.bashrc

ENV ATLAS_SWROOT=$ATLAS_SW_BASE/atlas.cern.ch/repo/sw


ARG BUILDARG_GCCVERSION
ARG ASG_ATHENA_RELEASENAME
ARG ASG_ATHENA_RELEASEVERSION
ARG ASG_ATHENA_RELEASEARCH

RUN source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh && lsetup pacman && lsetup swmgr && \
    sw-mgr -a gcc-x86_64:${BUILDARG_GCCVERSION} -i  ${BUILDARG_GCCVERSION} -n -o \
    --no-tag -p ${ATLAS_SWROOT}/atlas-gcc/$(echo ${BUILDARG_GCCVERSION}|sed 's|\.||g')/x86_64 \
    --site-config ${ATLAS_SWROOT}/AtlasSiteConfig.sh

RUN source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh && lsetup pacman && lsetup swmgr && \
    sw-mgr --autoconf ${ASG_ATHENA_RELEASENAME}:$ASG_ATHENA_RELEASEVERSION \
            --install ${ASG_ATHENA_RELEASEVERSION} \
            --physical $ATLAS_SWROOT/software/${ASG_ATHENA_RELEASENAME}/${ASG_ATHENA_RELEASEARCH}/${ASG_ATHENA_RELEASEVERSION} \
            --project-type release \
            --site-config ${ATLAS_SWROOT}/AtlasSiteConfig.sh \
            --no-tag \
            --relative-links

RUN sed -i "s|/cvmfs/atlas.cern.ch|$ATLAS_SW_BASE/atlas.cern.ch|g" $ATLAS_SW_BASE/atlas.cern.ch/repo/ATLASLocalRootBase/x86_64/AtlasSetup/.config/.asetup.site
RUN sed -i "s|^dbarea|\#dbarea|g" $ATLAS_SW_BASE/atlas.cern.ch/repo/ATLASLocalRootBase/x86_64/AtlasSetup/.config/.asetup.site
RUN sed -i "s|^dbrelease|\#dbrelease|g" $ATLAS_SW_BASE/atlas.cern.ch/repo/ATLASLocalRootBase/x86_64/AtlasSetup/.config/.asetup.site

USER root
RUN useradd atlas_user
USER atlas_user
WORKDIR /home/atlas_user
RUN echo "alias setupATLAS='source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh'" >> ~/.bashrc
