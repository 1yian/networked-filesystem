for i in {1..50}; do
	dd if=/dev/urandom of=file_$i bs=1M count=250
done
