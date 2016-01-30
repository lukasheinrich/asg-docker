FROM lukasheinrich/cern-root:latest
RUN apt-get install -y curl subversion flex bison nano
RUN mkdir /atlas-asg && cd /atlas-asg
WORKDIR /atlas-asg
ADD ./patches/TDT.patch /patches/TDT.patch
RUN curl http://physics.nyu.edu/~lh1132/rcSetup-00-04-16.tar.gz    | tar -xzvf - && \
    curl http://physics.nyu.edu/~lh1132/AnalysisBase-2.3.33.tar.gz | tar -xzvf - && \
    patch -p0 < /patches/TDT.patch && \
    curl http://physics.nyu.edu/~lh1132/AnalysisSUSY-2.3.33.tar.gz | tar -xzvf - && \
    ls AnalysisSUSY/2.3.33 | while read x; do rm -rf AnalysisBase/2.3.33/"$x";done && \
    mv AnalysisSUSY/2.3.33/* AnalysisBase/2.3.33 && \
    rm -rf AnalysisSUSY && \
    mv AnalysisBase AnalysisSUSY
RUN find -type d -iname .svn |while read x; do svn upgrade $(dirname $x);done || echo "ok go on gor now"
RUN cd /atlas-asg/AnalysisSUSY/2.3.33 && bash -c 'source RootCore/scripts/setup.sh && rc find_packages && rc build'
ADD get_rcsetup.sh /atlas-asg/get_rcsetup.sh
