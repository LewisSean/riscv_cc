
int add1(int b) {
	int a = b;
	return a;
}
int add(int a, int b) {
	int c=add1(b);
	return a + c;
}
int main() {
	int a = 5;
    int b =4;
    int c = add(a, 1);
    int d=add(a+c,a+b);
	if (a<3&&a+b>2) {
	    if (d>3){
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
    return 0;
}