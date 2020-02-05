FROM 018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-base
COPY get_lasrc_aux.sh ./usr/local/get_lasrc_aux.sh
ENV PREFIX=/usr/local \
	L8_AUX_DIR=/usr/local/src 

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["./usr/local/get_lasrc_aux.sh"]
