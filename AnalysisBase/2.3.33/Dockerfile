FROM lukasheinrich/cern-root:latest
RUN apt-get install -y curl subversion flex bison nano
RUN mkdir /atlas-asg && cd /atlas-asg
WORKDIR /atlas-asg
RUN curl http://physics.nyu.edu/~lh1132/rcSetup-00-04-16.tar.gz    | tar -xzvf - && \
    curl http://physics.nyu.edu/~lh1132/AnalysisBase-2.3.33.tar.gz | tar -xzvf -
RUN find -type d -iname .svn |while read x; do svn upgrade $(dirname $x);done
ADD ./patches/TDT.patch /patches/TDT.patch
RUN patch -p0 < /patches/TDT.patch
RUN cd /atlas-asg/AnalysisBase/2.3.33 && bash -c 'source RootCore/scripts/setup.sh && rc find_packages && rc build'
ADD get_rcsetup.sh /atlas-asg/get_rcsetup.sh