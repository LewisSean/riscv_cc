int main() {
	int a = 5;
	int b = 4;
	int c = 2;
	int d = a + b;
	if (a < 3||d>4) {
        a+=1;
        do{
            a-=2;
        }while(a<3);

        while(a>3){
            a+=2;
        }
	}
	else{
	    a+=3;
	}
	b = b + a;
}