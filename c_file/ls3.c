int a = 1000;
int main(int c ,int b){
int *p = &a;
*(p+1) = 1000;
*(p+1) = *(p + 3);
a = a + c * &b;
while(a < 100){
while(c > 100){
c = a + 100;
a = 10000;
}
}
int aaa = 1000;
return c;
}