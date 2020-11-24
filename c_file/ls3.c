
int a = 1000;
int main(int c ,int b){
a = a + c * b;
c = c * (a+b) + --b;
return c;
}