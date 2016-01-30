FROM lukasheinrich/cern-root:latest
RUN apt-get install -y curl subversion flex bison nano
RUN curl http://physics.nyu.edu/~lh1132/ASG_Docker.tar.gz | tar -xzvf - && mv ASG_Docker /atlas-asg
RUN find -type d -iname .svn |while read x; do svn upgrade $(dirname $x);done
ADD ./patches/TDT.patch /patches/TDT.patch
RUN patch -p0 < patches/TDT.patch 
RUN cd /atlas-asg/AnalysisBase/2.4.3 && bash -c 'source RootCore/scripts/setup.sh && rc find_packages && rc build'
ADD get_rcsetup.sh /atlas-asg/get_rcsetup.sh