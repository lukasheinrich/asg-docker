FROM lukasheinrich/cern-root:latest
RUN apt-get install -y curl subversion flex bison nano
RUN curl http://physics.nyu.edu/~lh1132/ASG_Docker.tar.gz | tar -xzvf - && mv ASG_Docker /atlas-asg
RUN find -type d -iname .svn |while read x; do svn upgrade $(dirname $x);done
ADD ./patches/TDT.patch /patches/TDT.patch
RUN patch -p0 < patches/TDT.patch 
RUN cd /atlas-asg/AnalysisBase/2.4.3 && bash -c 'source RootCore/scripts/setup.sh && rc find_packages && rc build'
ADD get_rcsetup.sh /atlas-asg/get_rcsetup.sh

RUN apt-get install -y cmake krb5-user krb5-config
RUN mkdir /code_xrootd && cd /code_xrootd && \
    git clone --depth 1 http://github.com/xrootd/xrootd.git -b v4.2.3 --single-branch && \
    cd xrootd && \
    mkdir xrootd-build && cd xrootd-build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local -DENABLE_PERL=FALSE -DENABLE_FUSE=FALSE && \
    make && make install && \
    curl -O https://raw.githubusercontent.com/betatim/everware-cern-analysis/master/krb5.conf && \
    cp krb5.conf /etc/krb5.conf
ENV LD_LIBRARY_PATH /usr/local/lib:$LD_LIBRARY_PATH

    


