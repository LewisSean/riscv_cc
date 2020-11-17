int go = 1000;
char ch = 'c';
int main(int c, int d){
int a = 1;
int b = 0;
int c = a + b;
L1:
b = c * a + (a+b)*b;
if(a<b || c > a + b){
a = b - 1;
}
else{
b = a - 1;
}
int i = 100;
while(i > 0){
b = b + a;
}
if(c > 100) goto L1;
return b;
}