# MongoDB Atlas Setup Guide

## Step 1: Create MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Click "Try Free" to create a free account
3. Sign up with your email or use Google/GitHub

## Step 2: Create a Cluster

1. After signing in, click "Build a Database"
2. Choose the **FREE** (M0) tier
3. Select a cloud provider and region (choose closest to you)
4. Name your cluster (e.g., "MovieMood-Cluster")
5. Click "Create Cluster" (takes 3-5 minutes)

## Step 3: Create Database User

1. In the Security section, click "Database Access"
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Enter a username and generate a secure password (save it!)
5. Set user privileges to "Atlas admin" or "Read and write to any database"
6. Click "Add User"

## Step 4: Configure Network Access

1. In the Security section, click "Network Access"
2. Click "Add IP Address"
3. For development, click "Allow Access from Anywhere" (0.0.0.0/0)
4. For production, add only your server's IP address
5. Click "Confirm"

## Step 5: Get Connection String

1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Select "Python" as the driver
4. Copy the connection string (looks like):
   ```
   mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<username>` with your database username
6. Replace `<password>` with your database password
7. Add your database name at the end:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/moviemood?retryWrites=true&w=majority
   ```

## Step 6: Update .env File

1. Copy `.env.example` to `.env`
2. Paste your MongoDB connection string:
   ```env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/moviemood?retryWrites=true&w=majority
   ```
3. Add your other API keys

## Step 7: Test Connection

Run the application:
```bash
python app.py
```

You should see:
```
✅ Successfully connected to MongoDB Atlas!
✅ Database indexes created successfully!
```

## Troubleshooting

### Connection Error
- Check your username and password are correct
- Verify IP address is whitelisted
- Check connection string format
- Ensure cluster is fully created (may take a few minutes)

### Authentication Error
- Verify database user credentials
- Check user has correct permissions
- Ensure password doesn't contain special characters that need URL encoding

### SSL/TLS Error
- MongoDB Atlas requires SSL by default
- Make sure `pymongo` is up to date: `pip install --upgrade pymongo`

## Database Collections

The application automatically creates these collections:
- **users**: User accounts and authentication
- **watchlist**: User's saved movies and shows
- **ratings**: User ratings and reviews

## Free Tier Limitations

- 512 MB storage
- Shared RAM and CPU
- Perfect for development and small applications
- Can handle thousands of users

## Production Considerations

1. **Security:**
   - Restrict IP access to your server only
   - Use strong passwords
   - Enable MongoDB Atlas security features

2. **Backup:**
   - Enable automated backups
   - Set up regular data exports

3. **Monitoring:**
   - Monitor database performance
   - Set up alerts for storage/usage

4. **Scaling:**
   - Upgrade to paid tier when needed
   - Consider read replicas for high traffic

## Need Help?

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [MongoDB Community Forum](https://www.mongodb.com/community/forums/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)

