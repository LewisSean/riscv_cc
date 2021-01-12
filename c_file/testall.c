struct Point{
    int x;
    int y;
};

struct Point1{
    int a;
    int b;
};

int add1(int b) {
	int a = b;
	return a;
}
int add(int a, int b) {
	int c = add1(b);
	return a + c;
}

int main() {
	int a = 1;
	int b = 2;

	int c[5] = { 1,2,3,4,6 };
	int cc[2][2] = { 1,2,3,4 };
	c[4] = 2;
	c[b] = 3;

	if (a+b < 3||c[4]>4) {
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

	int t = a+b;
	cc[1][2] = c[4]+c[2];
	cc[1][2] = c[2];

    struct Point1 point1 = { 1,2 };
    struct Point point ={3,4};
	int d = point.x + point1.a;

	int e=add(1,a);
	int f=add(a+b,e+1);
	a+=1;
	a-=1;
	a=a+b;
	a=a-b;
	a=a|b;
	a=a^b;
	a=a&b;
	a=a*b;
	a=a/b;
	a=a+1;
	a=1-b;
	a=c[1]|b;
	a=cc[1][1]^1;
	a=c[1]&point1.a;
    a=a++;
    a=a--;
    return 1;
}
