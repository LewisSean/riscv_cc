int add(int a, int b){
    return a + b;
}
int main() {
    int a = 5;
    int b =4;
    int c = add(a, b);
    add(a, c);
	if (a<3&&a+b>2) {
	    if (add(1,1)){
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