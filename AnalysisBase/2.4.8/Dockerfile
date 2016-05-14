FROM lukasheinrich/preasg-root
RUN yum install -y which
RUN mkdir /atlas-asg && cd /atlas-asg
WORKDIR /atlas-asg
RUN curl http://physics.nyu.edu/~lh1132/rcSetup-00-04-16.tar.gz    | tar -xzvf - && \
    curl http://physics.nyu.edu/~lh1132/AnalysisBase-2.4.8.tar.gz | tar -xzvf -
RUN cd /atlas-asg/AnalysisBase/2.4.8 && bash -c 'source /usr/local/bin/thisroot.sh && source RootCore/scripts/setup.sh && rc find_packages && rc build'
ADD get_rcsetup.sh /atlas-asg/get_rcsetup.sh
