int main() {
	int a = 5;
    int b =4;
	if (a<3&&a+b>2) {
	    if (a>2){
            a=a-1;
	    }
	    else{
	        a = a + 100;
	    }
	}
	else {
		a = a + 1;
		while(a  > 100){
		    a = a + 100;
		}
	}
    b = b + a;
}