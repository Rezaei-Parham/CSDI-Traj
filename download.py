BASEDIR /tmp/overlay-lab/lower0

RUN echo "BIB1" > file1.txt
RUN echo "BIB2" > file1.txt
RUN rm file1.txt
RUN echo "BIB3" > file3.txt
