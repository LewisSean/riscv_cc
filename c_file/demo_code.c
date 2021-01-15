int main(){
    int edge[6][6] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    int deg[6] = {0, 0, 0, 0, 0, 0};
    int que[6] = {0, 0, 0, 0, 0, 0};

    edge[1][2] = 1;
    edge[1][3] = 1;
    edge[2][4] = 1;
    edge[3][4] = 1;
    edge[4][5] = 1;
    deg[1] = 0;
    deg[2] = 1;
    deg[3] = 1;
    deg[4] = 2;
    deg[5] = 1;

    int n = 5;
    int l = 1;
    int r = 0;
    int cnt = 1;
    while(cnt <= n){
        if(deg[cnt] == 0) {
            r += 1;
            que[r] = cnt;
        }
        cnt += 1;
    }
    cnt = 0;
    int res[6] = {};
    while(l <= r){
        int u = que[l];
        l += 1;
        cnt += 1;
        res[++cnt] = u;
        int i = 1;
        while(i <= cnt){
            if(edge[u][i] != 0){
                deg[i] -= 1;
                if(deg[i] == 0){
                    r += 1;
                    que[r] = i;
                }
            }
            i += 1;
        }
    }
    return 0;
}